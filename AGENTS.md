# AGENTS.md



## Project Overview

Giftiaはギフト商品を検索するWebアプリケーションです。



Frontend

	Next.js (App Router)

	TypeScript

	React

Backend

	FastAPI

	SQLAlchemy

Database

	Azure MySQL

Main Features

	キーワード検索

	商品一覧表示

	商品詳細表示（今後実装予定）

	検索条件拡張（今後実装予定）



## Directory Structure

frontend/
├─ src/
│   ├─ app/
│   ├─ components/
│   ├─ lib/
│   └─ types/

backend/
├─ app/
│   ├─ routers/
│   ├─ services/
│   ├─ models/
│   ├─ database/
│   └─ schemas/

## Development Rules

Frontend

	App Routerを使用する

	Client Componentは必要な箇所のみ "use client" を付与する

	コンポーネントは単一責任を意識する

	API通信は lib/api.ts に集約する

	型定義は types フォルダへ配置する

Backend

	APIは /api/v1/ 配下に作成する

	SQLは直接書かずSQLAlchemyを使用する

	DB接続情報は .env で管理する

	Router → Service → Database の責務分離を行う



## Environment Variables

Frontend

	NEXT\_PUBLIC\_API\_URL=http://localhost:8000



Backend

	DB\_HOST=

	DB\_PORT=

	DB\_NAME=

	DB\_USER=

	DB\_PASSWORD=



## Running Locally

Frontend

	cd frontend

	npm install

	npm run dev

Backend

	cd backend

	pip install -r requirements.txt

	uvicorn app.main:app --reload

## Testing

Frontend

	npm run lint

	npm run build

Backend

	pytest



変更内容は必ず以下を満たすこと。

	Lintエラーなし

	TypeScriptエラーなし

	API起動確認済み

	検索機能の動作確認済み



## Coding Guidelines

TypeScript

	anyは禁止

	型を明示する

	Props型はinterfaceまたはtypeで定義する

Python

	PEP8準拠

	型ヒントを使用する

	関数は単一責任とする



## Search Feature

検索機能改修時は以下を確認すること。



Frontend

	検索キーワード取得

	API呼び出し

	ローディング表示

	エラーハンドリング

	検索結果表示

Backend

	クエリパラメータ取得

	バリデーション

	DB検索

	レスポンス整形

## Pull Request Checklist

TypeScriptエラーなし

Pythonエラーなし

ESLint通過

API動作確認済み

検索結果が正しく表示される

不要なconsole.logを削除した

.envをコミットしていない


## For AI Agents

コード修正時は以下を優先すること。

	既存のディレクトリ構成を維持する

	型安全性を損なわない

	API仕様を変更する場合はFrontendとBackend両方を更新する

	SQLインジェクション対策を維持する

	エラー時はユーザー向けメッセージを表示する

	ハードコーディングを避ける

	不明な場合は既存コードの命名規則に従う

