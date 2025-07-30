# databricks_rag_app_demo

## 概要

このプロジェクトは、DatabricksプラットフォームでRAG（Retrieval-Augmented Generation）アプリケーションを構築するためのデモワークショップです。PDFドキュメントのパース、ベクトルインデックスの作成、RAGエージェントの構築、そして最終的にWebアプリケーションのデプロイまでを一貫して学習できます。

## システム構成

本ワークショップで構築するRAGアプリケーションのシステム構成は以下の通りです：

```mermaid
flowchart TD
    EndUser["👤 エンドユーザー"]
    
    subgraph "Databricksプラットフォーム"
        subgraph "Databricks Workspace"
            Notebooks["📓 ノートブック群<br/>(1. PDFパース・ベクトル化<br/>2. RAGエージェント構築<br/>3. アプリデプロイ)"]
            WebApp["🌐 Webアプリケーション<br/>(Databricks Apps)"]
            
            subgraph "サービングエンドポイント"
                AgentEndpoint["🤖 RAG Agent<br/>(Model Serving)"]
                EmbedEndpoint["🧠 埋め込みモデル<br/>(Model Serving)"]
                LLMEndpoint["🧠 基盤モデル<br/>(Foundation Model API)"]
            end
        end
        
        subgraph "Unity Catalog"
            Files["📄 ファイル<br/>(PDFドキュメント)"]
            Tables["📊 テーブル<br/>(chunked_documents等)"]
            VectorIndex["🗃️ ベクトルインデックス<br/>(Vector Search)"]
            EmbedModel["🔧 埋め込みモデル<br/>(登録済みモデル)"]
            Agent["🤖 エージェント<br/>(登録済みエージェント)"]
        end
    end
    
    %% ユーザーとの関係
    EndUser --> WebApp
    
    %% ノートブックとUnity Catalogの関係
    Notebooks --> Files
    Notebooks --> Tables
    Notebooks --> VectorIndex
    Notebooks --> EmbedModel
    Notebooks --> Agent
    
    %% サービングエンドポイントとUnity Catalogの関係
    EmbedModel --> EmbedEndpoint
    Agent --> AgentEndpoint
    
    %% Webアプリとサービングエンドポイントの関係
    WebApp --> AgentEndpoint
    AgentEndpoint --> LLMEndpoint
    AgentEndpoint --> VectorIndex
    
    %% 埋め込みモデルエンドポイントとベクトルインデックスの関係
    EmbedEndpoint --> VectorIndex
    
    %% データ処理の流れ
    Files --> Tables
    Tables --> VectorIndex
    
    classDef userClass fill:#e8f5e8
    classDef workspaceClass fill:#e3f2fd
    classDef catalogClass fill:#fff3e0
    classDef notebookClass fill:#f3e5f5
    classDef appClass fill:#e0f2f1
    classDef servingClass fill:#fce4ec
    classDef dataClass fill:#f1f8e9
    classDef modelClass fill:#e8eaf6
    
    class EndUser userClass
    class Notebooks notebookClass
    class WebApp appClass
    class AgentEndpoint,EmbedEndpoint,LLMEndpoint servingClass
    class Files,Tables,VectorIndex dataClass
    class EmbedModel,Agent modelClass
```

### 主要コンポーネント

- **Unity Catalog**: データ・アセット管理基盤
  - ファイル（PDFドキュメント）の管理
  - テーブル（chunked_documents等）の管理
  - ベクトルインデックスの管理
  - 埋め込みモデル・エージェントの登録・管理
  
- **Databricks Workspace**: 開発・実行環境
  - ノートブック群（PDFパース〜アプリデプロイまでの一連の処理）
  - Webアプリケーション（Databricks Apps）
  - サービングエンドポイント（RAG Agent、埋め込みモデル、基盤モデル）

- **データフロー**: Unity Catalog内のアセットとWorkspace内のサービスが連携してRAGシステムを構成
- **全体基盤**: 全てのコンポーネントがDatabricksプラットフォーム上で完結

## 前提条件

### ワークスペース要件
このワークショップを実行するには、以下の機能が利用可能なリージョンのDatabricksワークスペースが必要です：

- **Databricks Apps**
- **Model Serving**
- **Vector Search**
- **Agent Framework**
- **Foundation Model API**

最新の対応状況については、リージョン限定の機能のドキュメント（[Azure](https://learn.microsoft.com/ja-jp/azure/databricks/resources/feature-region-support)/[AWS](https://docs.databricks.com/aws/ja/resources/feature-region-support)）をご確認ください。

### その他の要件
- Unity Catalogが有効化されたワークスペース
- 適切な権限を持つDatabricksアカウント

## 重要な注意事項

⚠️ **2025年7月時点で、このワークショップで使用される一部の機能はβ版です。**
- `ai_parse_document`関数

本番環境での使用前に、各機能の安定性とサポート状況をご確認ください。

## ファイル構成

### メインノートブック
このワークショップは3つのメインノートブックで構成されています：

1. **`1_PDFのパースとベクトルインデックスの作成.ipynb`**
   - PDFドキュメントの読み込みとテキスト抽出
   - テキストのチャンク化と前処理
   - Vector Searchを使用したベクトルインデックスの作成

2. **`2_RAGエージェントの構築.ipynb`**
   - Agent Frameworkを使用したRAGエージェントの実装
   - Model Servingエンドポイントとの連携
   - エージェントのテストと評価

3. **`3_Webアプリケーションのデプロイ.ipynb`**
   - Databricks Appsを使用したWebアプリケーションのデプロイ
   - ユーザーインターフェースの設定
   - アプリケーションの公開と管理

### サポートファイル

#### `input/`
サンプルPDFドキュメントが格納されているディレクトリ：
- `agent_system_design_pattern.pdf` - エージェントシステム設計パターン
- `genai_developver_workflow.pdf` - 生成AI開発ワークフロー

#### `streamlit_chatbot_sample/`
Streamlitを使用したチャットボットアプリケーションのサンプル：
- `app.py` - メインアプリケーションファイル
- `app.yaml` - Databricks Apps設定ファイル
- `messages.py` - メッセージ処理ロジック
- `model_serving_utils.py` - Model Servingとの連携ユーティリティ
- `requirements.txt` - Python依存関係

#### その他
- `agent.py` - RAGエージェントの実装
- `databricks.yml` - Databricksプロジェクト設定
- `参考_日本語埋め込みモデルのデプロイ.ipynb` - 日本語対応の埋め込みモデル参考資料

## 使用方法

1. **準備**
   - 対応リージョンのDatabricksワークスペースを用意
   - Unity Catalog上における利用可能なカタログを準備

2. **ワークショップの実行**
   - ノートブック1から順番に実行
   - 各ステップで生成されるリソースを確認

3. **アプリケーションのデプロイ**
   - ノートブック3を参考にしながらWebアプリケーションをデプロイ

## 参考リンク

- [Databricks機能のリージョンサポート（Azure）](https://learn.microsoft.com/ja-jp/azure/databricks/resources/feature-region-support)
- [Databricks機能のリージョンサポート（AWS）](https://docs.databricks.com/aws/ja/resources/feature-region-support#model-serving-aws)
- [Databricks Apps ドキュメント](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html)
- [Agent Framework ドキュメント](https://docs.databricks.com/en/generative-ai/agent-framework/index.html)