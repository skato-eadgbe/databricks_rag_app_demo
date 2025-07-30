"""
Databricks Tool-calling RAG Agent Implementation

このファイルは、LangGraphとMosaic AI Agent Frameworkを使用した
高度なTool-calling RAGエージェントの実装です。

主な機能:
- Vector Searchを活用した文書検索
- Unity Catalog Functionとの統合
- マルチターン会話の管理
- ストリーミング対応
"""

from typing import Any, Generator, Optional, Sequence, Union

import mlflow
from databricks_langchain import (
    ChatDatabricks,
    VectorSearchRetrieverTool,
    DatabricksFunctionClient,
    UCFunctionToolkit,
    set_uc_function_client,
)
from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.tool_node import ToolNode
from mlflow.langchain.chat_agent_langgraph import ChatAgentState, ChatAgentToolNode
from mlflow.pyfunc import ChatAgent
from mlflow.types.agent import (
    ChatAgentChunk,
    ChatAgentMessage,
    ChatAgentResponse,
    ChatContext,
)

# MLflowの自動ログ機能を有効化
mlflow.langchain.autolog()

# Unity Catalog Function用のクライアント設定
client = DatabricksFunctionClient()
set_uc_function_client(client)

############################################
# LLMエンドポイントとシステムプロンプトの定義
############################################
LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4"
llm = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)

# システムプロンプト: エージェントの基本的な動作を定義
system_prompt = """あなたは生成AI開発に関する専門的なアシスタントです。
登録されたVector Search Indexを活用して、
ユーザーの質問に対して正確で有用な回答を提供してください。

以下のガイドラインに従ってください：
1. 利用可能なツールを効果的に活用してください
2. 検索された文書の内容に基づいて回答してください  
3. 不確かな情報については推測を避けてください
4. 具体的で実用的なアドバイスを提供してください
5. 日本語で丁寧に回答してください

必要に応じて複数のツールを組み合わせて使用し、
ユーザーにとって最も有益な情報を提供してください。"""

###############################################################################
## エージェントツールの定義
## テキスト生成以外のデータ取得やアクション実行を可能にするツール群
## 詳細な例については以下のドキュメントを参照:
## https://learn.microsoft.com/azure/databricks/generative-ai/agent-framework/agent-tool
###############################################################################
tools = []

# Unity CatalogのUDFをエージェントツールとして使用
# 必要に応じて関数名を追加してください
uc_tool_names = []
uc_toolkit = UCFunctionToolkit(function_names=uc_tool_names)
tools.extend(uc_toolkit.tools)

# Vector Search Indexごとにretrieverツールを作成
# 詳細: https://learn.microsoft.com/azure/databricks/generative-ai/agent-framework/unstructured-retrieval-tools
vector_search_index_tools = [
    VectorSearchRetrieverTool(
        index_name="skato.rag_workshop.chunked_document_vs_index",
        tool_description="生成AI開発に関する技術文書やベストプラクティスを検索するためのツールです。GenAI開発ワークフロー、MLOps、エージェント設計などについて質問がある場合に使用してください。"
    )
]
tools.extend(vector_search_index_tools)

#####################
## エージェントロジックの定義
#####################

def create_tool_calling_agent(
    model: LanguageModelLike,
    tools: Union[Sequence[BaseTool], ToolNode],
    system_prompt: Optional[str] = None,
) -> CompiledGraph:
    """
    Tool-calling機能を持つエージェントを作成

    Args:
        model: 使用するLLMモデル
        tools: エージェントが使用可能なツールのリスト
        system_prompt: システムプロンプト

    Returns:
        コンパイル済みのLangGraphワークフロー
    """
    # モデルにツールをバインド
    model = model.bind_tools(tools)

    # 次のノードを決定する関数
    def should_continue(state: ChatAgentState):
        """
        エージェントがツールを呼び出すかどうかを判定
        """
        messages = state["messages"]
        last_message = messages[-1]
        # Function callがある場合は継続、そうでなければ終了
        if last_message.get("tool_calls"):
            return "continue"
        else:
            return "end"

    # システムプロンプトの前処理
    if system_prompt:
        preprocessor = RunnableLambda(
            lambda state: [{"role": "system", "content": system_prompt}]
            + state["messages"]
        )
    else:
        preprocessor = RunnableLambda(lambda state: state["messages"])

    model_runnable = preprocessor | model

    def call_model(
        state: ChatAgentState,
        config: RunnableConfig,
    ):
        """
        LLMモデルを呼び出し、レスポンスを処理
        """
        response = model_runnable.invoke(state, config)
        return {"messages": [response]}

    # LangGraphワークフローの構築
    workflow = StateGraph(ChatAgentState)

    # ノードの追加
    workflow.add_node("agent", RunnableLambda(call_model))
    workflow.add_node("tools", ChatAgentToolNode(tools))

    # エントリーポイントの設定
    workflow.set_entry_point("agent")

    # 条件分岐エッジの追加
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",  # ツール実行へ
            "end": END,          # 処理終了
        },
    )

    # ツールからエージェントへのエッジ
    workflow.add_edge("tools", "agent")

    return workflow.compile()


class LangGraphChatAgent(ChatAgent):
    """
    MLflow ChatAgentインターフェースを実装したLangGraphエージェント

    マルチターン会話とストリーミング対応を提供
    """

    def __init__(self, agent: CompiledStateGraph):
        self.agent = agent

    def predict(
        self,
        messages: list[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[dict[str, Any]] = None,
    ) -> ChatAgentResponse:
        """
        同期的な予測処理

        Args:
            messages: 会話履歴
            context: 追加のコンテキスト情報
            custom_inputs: カスタム入力パラメータ

        Returns:
            ChatAgentResponse: エージェントの応答
        """
        request = {"messages": self._convert_messages_to_dict(messages)}

        messages = []
        # ワークフローを実行し、すべての更新を収集
        for event in self.agent.stream(request, stream_mode="updates"):
            for node_data in event.values():
                messages.extend(
                    ChatAgentMessage(**msg) for msg in node_data.get("messages", [])
                )
        return ChatAgentResponse(messages=messages)

    def predict_stream(
        self,
        messages: list[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[dict[str, Any]] = None,
    ) -> Generator[ChatAgentChunk, None, None]:
        """
        ストリーミング予測処理

        Args:
            messages: 会話履歴
            context: 追加のコンテキスト情報
            custom_inputs: カスタム入力パラメータ

        Yields:
            ChatAgentChunk: エージェントの応答チャンク
        """
        request = {"messages": self._convert_messages_to_dict(messages)}
        # ワークフローをストリーミング実行
        for event in self.agent.stream(request, stream_mode="updates"):
            for node_data in event.values():
                yield from (
                    ChatAgentChunk(**{"delta": msg}) for msg in node_data["messages"]
                )


# エージェントオブジェクトの作成
# MLflow推論時に使用するエージェントとして設定
agent = create_tool_calling_agent(llm, tools, system_prompt)
AGENT = LangGraphChatAgent(agent)
mlflow.models.set_model(AGENT)