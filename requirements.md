# Databricks RAGアプリチュートリアル　要件定義書

## 概要

- PDFをパースし、Vector Search Indexに登録し、RAG Agentを行うワークショップのコンテンツを実装する。

## 実行環境・前提

- Databricksで実行する
- Databricksノートブックは、%sqlのマジックコマンドを入れることでSQLを実行することも可能
- ワークショップに使うノートブックであるため、各ステップにおいて使用する機能についてはmarkdownで簡単な解説を入れる

## 実装内容

### 1. ワークショップ用ノートブック

#### 1-1. パラメータの設定

- 使用するカタログ、スキーマを指定する。カタログは既存のものを使用し、スキーマは既存のものの利用と新規作成の両方に対応する。後続の作業で必要なパラメータもここで管理する。

#### 1-2. PDFのパース、前処理、Unity Catalogテーブル登録


- PDFを`ai_parse_document`関数を用いてパースし、チャンキング等の前処理を行った上でUnity Catalogにテーブルとして保存する。pysparkではなく、ノートブックに%sqlシンタックスをつけSQLで実行する。
- パースしたコンテンツは、ベストプラクティスに従ってチャンキングが必要かを考える。チャンキング戦略はこちらを確認する https://docs.databricks.com/aws/en/generative-ai/tutorials/ai-cookbook/quality-data-pipeline-rag
- `ai_parse_document`関数自体の解説も含める。
- pdfの構造は/Users/shoki.kato/dev/databricks/databricks_rag_app_demo/sample/genai_developver_workflow.pdfを参照すること。
- 参考：https://docs.databricks.com/aws/ja/sql/language-manual/functions/ai_parse_document

#### 1-3. Vector Search Indexの作成

- Mosaic AI Vector Searchのインデックスを作成する
- UIでの作成手順をまず補足し、その後Python SDKでの実装サンプルをノートブックに含める。
- Vector Searchエンドポイントは既存のものを使用するか、新規に作成するか選べるようにする。インデックスは必ず新規に作成する。
- Embeddingに使用するモデルは、sample/[Fix]create_endpoint_for_pfnet_plamo-embedding-1b.ipynb でサービングするモデルを使用する前提とする
- 参考：https://docs.databricks.com/aws/en/generative-ai/create-query-vector-search

#### 1-4. Vector Searchのテスト

- まず、Python SDKにより類似度検索のクエリを作成したクエリに実行する
- 次に、SQLの`vector_search`関数を用いて検索する。使い方はhttps://docs.databricks.com/gcp/ja/sql/language-manual/functions/vector_search を参照する

### RAGアプリケーション実装用ノートブック

下記はガイドであり、このノートブックの構成はベストプラクティスに合わせる

#### 2-1. パラメータの設定

- 基本は1-1に合わせる
- MLflow 3.0>以上のバージョンを使用する

#### 2-2. RAG Agentの作成
- 1で作成したアウトプット（Vector Search）に対してドキュメントを検索するシンプルなエージェントを作成する。
- 手順はベストプラクティスに任せる。
- Mosaic AI Agent Frameworkと、Mosaic AI Agent Evaluationを活用する。
- 参考：https://docs.databricks.com/aws/ja/generative-ai/agent-framework/author-agent

#### 2-3. RAG Agentの評価

- MLflow 3.0による、LLM as judgeによる評価のデモを行う
- 人間による評価のデモンストレーションを行う
- https://docs.databricks.com/aws/en/mlflow3/genai/agent-eval-migration


