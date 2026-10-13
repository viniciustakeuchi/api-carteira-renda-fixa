from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.deps import Sessao, UsuarioAtual
from app.models import Usuario
from app.schemas import Token, UsuarioCriar, UsuarioSaida
from app.security import criar_token, gerar_hash, verificar_senha

router = APIRouter(prefix="/auth", tags=["autenticação"])


@router.post("/registro", response_model=UsuarioSaida, status_code=status.HTTP_201_CREATED)
async def registrar(dados: UsuarioCriar, sessao: Sessao) -> Usuario:
    existente = await sessao.scalar(select(Usuario).where(Usuario.email == dados.email))
    if existente:
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    usuario = Usuario(nome=dados.nome, email=dados.email, senha_hash=gerar_hash(dados.senha))
    sessao.add(usuario)
    await sessao.commit()
    return usuario


@router.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], sessao: Sessao) -> Token:
    usuario = await sessao.scalar(select(Usuario).where(Usuario.email == form.username))
    if usuario is None or not verificar_senha(form.password, usuario.senha_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=criar_token(usuario.id))


@router.get("/me", response_model=UsuarioSaida)
async def me(usuario: UsuarioAtual) -> Usuario:
    return usuario
