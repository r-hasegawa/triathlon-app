"""
ユーザー一括登録エンドポイント
CSVファイルからユーザーを一括インポート
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, AdminUser
from app.utils.dependencies import get_current_admin
from app.utils.security import get_password_hash
from typing import List
import csv
import io
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator

router = APIRouter()

# スキーマ定義
class UserImportRecord(BaseModel):
    """インポートするユーザーレコード"""
    user_id: str
    username: str
    full_name: str
    email: EmailStr
    password: str
    
    @field_validator('user_id', 'username', 'full_name', 'password')
    @classmethod
    def validate_not_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f'{info.field_name} cannot be empty')
        return v.strip()

class ImportResult(BaseModel):
    """インポート結果"""
    success: bool
    total_records: int
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[dict]
    imported_users: List[dict]

class ImportErrorDetail(BaseModel):
    """エラー詳細"""
    row: int
    user_id: str
    username: str
    error: str

@router.post("/import-users", response_model=ImportResult)
async def import_users_from_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """
    CSVファイルからユーザーを一括インポート
    
    CSVフォーマット:
    ID,user_name,full_name,e-mail,password
    user001,tanaka,田中太郎,tanaka@example.com,password123
    user002,sato,佐藤花子,sato@example.com,password456
    
    ヘッダー行は必須
    各カラムは空白不可
    """
    
    # ファイル検証
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    # CSVファイル読み込み
    try:
        content = await file.read()
        decoded_content = content.decode('utf-8-sig')  # BOM対応
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
    except UnicodeDecodeError:
        # UTF-8で失敗した場合、Shift-JISを試す
        try:
            decoded_content = content.decode('shift-jis')
            csv_reader = csv.DictReader(io.StringIO(decoded_content))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File encoding error. Please use UTF-8 or Shift-JIS: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read CSV file: {str(e)}"
        )
    
    # ヘッダー検証
    expected_headers = {'ID', 'user_name', 'full_name', 'e-mail', 'password'}
    if not csv_reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file has no headers"
        )
    
    actual_headers = set(csv_reader.fieldnames)
    if not expected_headers.issubset(actual_headers):
        missing = expected_headers - actual_headers
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required columns: {', '.join(missing)}"
        )
    
    # インポート処理
    total_records = 0
    imported_count = 0
    skipped_count = 0
    error_count = 0
    errors: List[dict] = []
    imported_users: List[dict] = []
    
    for row_num, row in enumerate(csv_reader, start=2):  # ヘッダーが1行目なので2から開始
        total_records += 1
        
        try:
            # データ抽出
            user_id = row['ID'].strip()
            username = row['user_name'].strip()
            full_name = row['full_name'].strip()
            email = row['e-mail'].strip()
            password = row['password'].strip()
            
            # 必須項目チェック
            if not all([user_id, username, full_name, email, password]):
                errors.append({
                    "row": row_num,
                    "user_id": user_id,
                    "username": username,
                    "error": "All fields are required"
                })
                error_count += 1
                continue
            
            # 既存ユーザーチェック
            existing_user = db.query(User).filter(
                (User.user_id == user_id) | 
                (User.username == username) |
                (User.email == email)
            ).first()
            
            if existing_user:
                errors.append({
                    "row": row_num,
                    "user_id": user_id,
                    "username": username,
                    "error": f"User already exists (conflict with: {existing_user.user_id})"
                })
                skipped_count += 1
                continue
            
            # ユーザー作成
            new_user = User(
                user_id=user_id,
                username=username,
                full_name=full_name,
                email=email,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_admin=False
            )
            
            db.add(new_user)
            imported_count += 1
            
            imported_users.append({
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "email": email
            })
            
        except Exception as e:
            errors.append({
                "row": row_num,
                "user_id": row.get('ID', 'N/A'),
                "username": row.get('user_name', 'N/A'),
                "error": str(e)
            })
            error_count += 1
    
    # データベースにコミット
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during commit: {str(e)}"
        )
    
    return ImportResult(
        success=error_count == 0,
        total_records=total_records,
        imported_count=imported_count,
        skipped_count=skipped_count,
        error_count=error_count,
        errors=errors,
        imported_users=imported_users
    )