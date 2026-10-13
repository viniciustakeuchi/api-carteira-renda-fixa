from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Usuario
from app.security import ler_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")

Sessao = Annotated[AsyncSession, Depends(get_session)]


async def usuario_atual(token: Annotated[str, Depends(oauth2)], sessao: Sessao) -> Usuario:
    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    usuario_id = ler_token(token)
    if usuario_id is None:
        raise erro
    usuario = await sessao.get(Usuario, usuario_id)
    if usuario is None:
        raise erro
    return usuario


UsuarioAtual = Annotated[Usuario, Depends(usuario_atual)]
