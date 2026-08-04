# FeedPet

Aplicação web para cadastro, divulgação e acompanhamento de animais disponíveis para adoção.

O projeto foi desenvolvido com Django e organiza o fluxo desde o cadastro do pet até a atualização do status de adoção, com área administrativa, autenticação e galeria pública.

## Funcionalidades

- cadastro e autenticação de usuários;
- acesso de visitante à galeria;
- cadastro, edição e remoção de animais;
- filtros e paginação na galeria;
- páginas individuais com URLs amigáveis;
- upload de foto principal, galeria adicional e vídeo;
- estados de adoção: pendente, disponível, em processo e adotado;
- aprovação e gerenciamento pela área administrativa;
- relatório restrito a usuários da equipe;
- geração opcional de uma prévia estática para publicação.

## Tecnologias

- Python 3.11+
- Django 5
- SQLite para desenvolvimento local
- Pillow para processamento de imagens
- HTML e templates Django
- Bootstrap

## Executando localmente

```bash
git clone https://github.com/mmatteuus/feedpet.git
cd feedpet
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Instale as dependências e prepare o banco:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

A aplicação ficará disponível em `http://127.0.0.1:8000`.

## Variáveis de ambiente

Em produção, configure pelo menos:

```env
DJANGO_SECRET_KEY=troque-por-uma-chave-segura
DJANGO_DEBUG=0
```

O banco local, arquivos enviados pelos usuários, ambientes virtuais e artefatos compilados não são versionados.

## Estrutura principal

```text
adocoes/        domínio, modelos, formulários, views e rotas
core/           configuração do projeto Django
templates/      páginas HTML
media/          arquivos de demonstração utilizados na prévia estática
build_static.py geração opcional da prévia estática
```

## Próximas melhorias

- ampliar a cobertura de testes automatizados;
- utilizar PostgreSQL e armazenamento externo em produção;
- adicionar notificações para interessados e responsáveis;
- registrar o histórico completo do processo de adoção.

---

Projeto de portfólio desenvolvido por Mateus Ferreira Lopes.