
import asyncio
import os
import platform
import requests
import time
from fastapi import APIRouter
from pathlib import Path
from typing import Literal

from app import schemas
from app.constants import API_REQUEST_HEADERS, CONFIG, VERSION


# ルーター
router = APIRouter(
    tags = ['Version'],
    prefix = '/api/version',
)


# GitHub API から取得した KonomiTV の最新バージョン (と最終更新日時)
latest_version: str | None = None
latest_version_updated_at: float = 0


@router.get(
    '',
    summary = 'バージョン情報取得 API',
    response_description = 'KonomiTV サーバーのバージョンなどの情報。',
    response_model = schemas.VersionInformation,
)
async def VersionInformationAPI():
    """
    KonomiTV サーバーのバージョン情報と、バックエンドの種類、稼働環境などを取得する。
    """

    global latest_version, latest_version_updated_at

    # GitHub API で KonomiTV の最新のタグ (=最新バージョン) を取得
    ## GitHub API は無認証だと60回/1時間までしかリクエストできないので、リクエスト結果を10分ほどキャッシュする
    if latest_version is None or (time.time() - latest_version_updated_at) > 60 * 10:
        try:
            response = await asyncio.to_thread(requests.get,
                url = 'https://api.github.com/repos/tsukumijima/KonomiTV/tags',
                headers = API_REQUEST_HEADERS,
                timeout = 3,
            )
            if response.status_code == 200:
                latest_version = response.json()[0]['name'].replace('v', '')  # 先頭の v を取り除く
                latest_version_updated_at = time.time()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

    # サーバーが稼働している環境を取得
    environment: Literal['Windows', 'Linux', 'Linux-Docker', 'Linux-ARM'] = 'Windows' if os.name == 'nt' else 'Linux'
    if environment == 'Linux' and Path.exists(Path('/.dockerenv')) is True:
        # Linux かつ Docker 環境
        environment = 'Linux-Docker'
    if environment == 'Linux' and platform.machine() == 'aarch64':
        # Linux かつ ARM 環境
        environment = 'Linux-ARM'

    return {
        'version': VERSION,
        'latest_version': latest_version,
        'environment': environment,
        'backend': CONFIG['general']['backend'],
        'encoder': CONFIG['general']['encoder'],
    }
