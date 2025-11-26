"""
Script para popular o banco com dados de exemplo
Execute após subir o ambiente: python seed_data.py
"""
import requests
import time

API_URL = "http://localhost:8000"

# Dados de exemplo
AUTHORS = [
    {
        "name": "Maria Silva",
        "email": "maria.silva@example.com",
        "bio": "Engenheira de dados especializada em cloud computing e big data."
    },
    {
        "name": "João Santos",
        "email": "joao.santos@example.com",
        "bio": "Arquiteto de soluções AWS com foco em bancos de dados e cache."
    },
    {
        "name": "Ana Costa",
        "email": "ana.costa@example.com",
        "bio": "Tech lead com expertise em sistemas distribuídos e performance."
    }
]

POSTS = [
    {
        "title": "Introdução ao Amazon RDS",
        "slug": "introducao-amazon-rds",
        "summary": "Aprenda os fundamentos do serviço de banco de dados relacional da AWS.",
        "content": """
# Introdução ao Amazon RDS

Amazon RDS (Relational Database Service) é um serviço gerenciado que facilita a configuração,
operação e escalabilidade de bancos de dados relacionais na nuvem.

## Principais Benefícios

- **Gerenciamento automatizado**: Backups, patches e atualizações automáticas
- **Alta disponibilidade**: Multi-AZ deployments para failover automático
- **Escalabilidade**: Ajuste de recursos com poucos cliques
- **Segurança**: Criptografia em repouso e em trânsito

## Engines Suportadas

- PostgreSQL
- MySQL
- MariaDB
- Oracle
- SQL Server
- Aurora (compatível com PostgreSQL e MySQL)

Este workshop foca em PostgreSQL, um dos bancos mais populares para aplicações modernas.
        """,
        "author_id": 1,
        "published": True
    },
    {
        "title": "Redis e ElastiCache: Cache de Alto Desempenho",
        "slug": "redis-elasticache-cache-alto-desempenho",
        "summary": "Descubra como Redis e ElastiCache podem acelerar suas aplicações.",
        "content": """
# Redis e ElastiCache

Redis é um armazenamento de estrutura de dados em memória, usado como banco de dados,
cache e message broker. Amazon ElastiCache for Redis facilita o deploy e gerenciamento.

## Por que usar Cache?

- **Redução de latência**: Respostas em milissegundos vs segundos
- **Redução de carga**: Menos queries no banco de dados principal
- **Economia de custos**: Menor uso de IOPS e CPU no RDS

## Padrões de Cache

### Cache-Aside (Lazy Loading)
1. Aplicação busca no cache
2. Se não encontrar (cache miss), busca no banco
3. Armazena resultado no cache
4. Próximas requisições pegam do cache (cache hit)

### Write-Through
Ao modificar dados, atualiza banco E cache simultaneamente.

### Cache com TTL
Define tempo de expiração para renovação automática dos dados.

## Casos de Uso

- Session store
- Contadores em tempo real
- Leaderboards/rankings
- Rate limiting
- Pub/Sub messaging
        """,
        "author_id": 2,
        "published": True
    },
    {
        "title": "Padrões de Integração PostgreSQL + Redis",
        "slug": "padroes-integracao-postgresql-redis",
        "summary": "Melhores práticas para combinar banco relacional com cache.",
        "content": """
# Padrões de Integração PostgreSQL + Redis

A combinação de PostgreSQL (durabilidade) com Redis (velocidade) oferece o melhor dos dois mundos.

## Arquitetura Recomendada

```
Cliente → API → Redis (Cache) → PostgreSQL (Dados)
                    ↓
              Dados temporários
              (contadores, sessões)
```

## Quando usar cada um?

### Use PostgreSQL para:
- Dados que precisam ser persistidos
- Transações ACID
- Consultas complexas com JOINs
- Dados históricos e relatórios

### Use Redis para:
- Cache de queries frequentes
- Contadores em tempo real
- Dados temporários (sessões)
- Filas e mensageria
- Rate limiting

## Estratégias de Consistência

### Eventual Consistency
Dados podem estar temporariamente dessincronizados entre cache e banco.
Aceitável para a maioria dos casos (ex: contadores de views).

### Strong Consistency
Invalida cache imediatamente ao modificar dados.
Necessário para dados críticos (ex: saldo bancário).

## Persistência Assíncrona

Mantenha contadores no Redis para performance e persista periodicamente
no PostgreSQL para análise histórica.

**Exemplo**: Views de posts incrementadas no Redis a cada visualização,
persistidas no PostgreSQL uma vez por hora via cronjob.
        """,
        "author_id": 3,
        "published": True
    },
    {
        "title": "Monitoramento e Observabilidade na AWS",
        "slug": "monitoramento-observabilidade-aws",
        "summary": "Como monitorar RDS e ElastiCache em produção.",
        "content": """
# Monitoramento e Observabilidade

Monitorar seus bancos de dados e cache é essencial para manter performance e disponibilidade.

## CloudWatch Metrics

### RDS PostgreSQL
- DatabaseConnections
- ReadLatency / WriteLatency
- ReadIOPS / WriteIOPS
- FreeStorageSpace
- CPUUtilization

### ElastiCache Redis
- CacheHits / CacheMisses (taxa de acerto do cache)
- Evictions (itens removidos por falta de memória)
- CurrConnections
- NetworkBytesIn / NetworkBytesOut
- CPUUtilization

## Alarmes Importantes

1. **Cache Hit Rate < 80%**: Cache pode não estar efetivo
2. **RDS CPU > 80%**: Pode precisar escalar
3. **Redis Memory > 90%**: Risco de evictions
4. **RDS Connections > 80% do máximo**: Pool de conexões cheio

## Performance Insights

Use RDS Performance Insights para identificar queries lentas e gargalos.

## Logs

- Enable slow query logs no PostgreSQL
- Configure Redis logs para debugging
- Centralize com CloudWatch Logs
        """,
        "author_id": 1,
        "published": True
    },
    {
        "title": "Segurança em RDS e ElastiCache",
        "slug": "seguranca-rds-elasticache",
        "summary": "Boas práticas de segurança para seus dados na AWS.",
        "content": """
# Segurança em RDS e ElastiCache

Proteger seus dados é fundamental. A AWS oferece várias camadas de segurança.

## Network Security

### VPC e Security Groups
- Nunca exponha RDS/ElastiCache publicamente
- Use VPC privada
- Security groups restritivos (apenas portas necessárias)
- Acesso apenas de subnets específicas

### Exemplo de Arquitetura Segura
```
Internet → ALB (public subnet)
            ↓
       ECS/Lambda (private subnet)
            ↓
    RDS + ElastiCache (private subnet)
```

## Encryption

### Em Repouso
- Enable encryption at rest no RDS
- Use KMS (Key Management Service)
- ElastiCache Redis também suporta encryption

### Em Trânsito
- Force SSL/TLS connections
- PostgreSQL: require_ssl = on
- Redis: use TLS endpoints

## Authentication & Authorization

### RDS
- Nunca use senha padrão
- Rotação de senhas regular
- IAM database authentication quando possível
- Princípio do menor privilégio (least privilege)

### Redis
- Enable AUTH
- Use Redis 6+ com ACLs para controle granular

## Backup e Recovery

- Automated backups habilitados
- Retention period adequado (7-35 dias)
- Teste recovery procedures periodicamente
- Consider cross-region backups para DR

## Compliance

- Enable CloudTrail para auditoria
- VPC Flow Logs
- Database activity streams (RDS)
        """,
        "author_id": 2,
        "published": True
    },
    {
        "title": "Otimização de Custos: RDS e ElastiCache",
        "slug": "otimizacao-custos-rds-elasticache",
        "summary": "Dicas para reduzir custos mantendo performance.",
        "content": """
# Otimização de Custos

Como obter máximo valor dos seus recursos AWS sem comprometer performance.

## RDS Cost Optimization

### Right-Sizing
- Monitore métricas de uso (CPU, Memory, IOPS)
- Não super-provisione
- Use Compute Optimizer recommendations

### Storage
- General Purpose (gp3) vs Provisioned IOPS (io1)
- gp3 é mais custo-efetivo para maioria dos casos
- Delete snapshots antigos

### Reserved Instances
- Economize até 60% com commitment de 1-3 anos
- Ideal para ambientes de produção estáveis

### Aurora Serverless
- Para workloads intermitentes
- Paga apenas quando usa

## ElastiCache Cost Optimization

### Node Types
- Escolha tipo adequado (memory-optimized)
- Não pague por capacidade não utilizada

### Reserved Nodes
- Mesma lógica do RDS
- Economias significativas

### Cache Hit Rate
- Melhore cache hit rate (menos queries no RDS)
- Cada cache hit economiza uma query no banco

### TTL Adequado
- TTL muito baixo: mais queries no banco
- TTL muito alto: dados desatualizados
- Balance baseado no caso de uso

## Boas Práticas

1. **Use cache agressivamente**: Cada query evitada economiza $
2. **Monitore constantemente**: Identifique recursos sub-utilizados
3. **Automatize scale down**: Reduza recursos fora do horário de pico
4. **Delete recursos não utilizados**: Ambientes de dev/test

## Exemplo de Economia

Cenário: API com 1000 req/s

**Sem cache**:
- 1000 queries/s no RDS
- RDS db.r6g.2xlarge necessário
- ~$700/mês

**Com cache (90% hit rate)**:
- 100 queries/s no RDS
- RDS db.r6g.large suficiente (~$350/mês)
- ElastiCache cache.r6g.large (~$200/mês)
- **Total: $550/mês (economia de 21%)**

Além disso: melhor latência e experiência do usuário!
        """,
        "author_id": 3,
        "published": True
    },
    {
        "title": "Workshop Prático: Construindo uma API Escalável",
        "slug": "workshop-api-escalavel",
        "summary": "Hands-on: Como construímos este sistema de blog.",
        "content": """
# Workshop Prático

Este próprio sistema de blog é um exemplo funcional de tudo que discutimos!

## Stack Tecnológica

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Containerização**: Docker
- **Deploy**: AWS ECS + RDS + ElastiCache

## Funcionalidades Demonstradas

### 1. Cache-Aside Pattern
```python
# Busca post por ID
GET /posts/{id}

# Fluxo:
1. Busca no Redis
2. Se não encontrar → busca PostgreSQL
3. Armazena no Redis
4. Retorna resultado
```

### 2. Contadores em Tempo Real
```python
# Incrementa views
GET /posts/{id}?increment_view=true

# Cada acesso incrementa contador no Redis
# Muito mais rápido que UPDATE no PostgreSQL
```

### 3. Rankings Dinâmicos
```python
# Top posts mais visualizados
GET /stats/top-posts

# Combina:
- Contadores do Redis
- Metadados do PostgreSQL
- Cache de 1 minuto
```

### 4. Persistência Assíncrona
```python
# Persiste contadores
POST /stats/persist-views

# Move dados Redis → PostgreSQL
# Para análise histórica
```

## Testando o Sistema

1. **Crie alguns autores e posts**
2. **Acesse posts várias vezes** (incrementa views)
3. **Veja o ranking atualizar** em tempo real
4. **Persista os contadores** no PostgreSQL
5. **Observe o cache funcionando** (response time)

## Código Aberto

Todo o código está disponível. Explore:
- `src/services.py`: Lógica de cache
- `src/routes/`: Endpoints da API
- `docker-compose.yml`: Setup local

## Próximos Passos

- Deploy na AWS (ECS + RDS + ElastiCache)
- Adicione CI/CD pipeline
- Implemente autenticação
- Adicione testes automatizados
- Configure monitoramento

**Divirta-se explorando!** 🚀
        """,
        "author_id": 1,
        "published": True
    }
]


def wait_for_api():
    """Aguarda API ficar disponível"""
    print("⏳ Aguardando API ficar disponível...")
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get(f"{API_URL}/health")
            if response.status_code == 200:
                print("✅ API disponível!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    print("❌ API não ficou disponível")
    return False


def seed_authors():
    """Cria autores de exemplo"""
    print("\n📝 Criando autores...")
    author_ids = []

    for author in AUTHORS:
        try:
            response = requests.post(f"{API_URL}/authors/", json=author)
            if response.status_code == 201:
                data = response.json()
                author_ids.append(data['id'])
                print(f"   ✓ {author['name']} (ID: {data['id']})")
            else:
                print(f"   ✗ Erro ao criar {author['name']}: {response.text}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")

    return author_ids


def seed_posts(author_ids):
    """Cria posts de exemplo"""
    print("\n📰 Criando posts...")

    for i, post in enumerate(POSTS):
        # Distribui posts entre autores
        post['author_id'] = author_ids[i % len(author_ids)]

        try:
            response = requests.post(f"{API_URL}/posts/", json=post)
            if response.status_code == 201:
                data = response.json()
                print(f"   ✓ {post['title'][:50]}... (ID: {data['id']})")
            else:
                print(f"   ✗ Erro ao criar post: {response.text}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")


def simulate_views():
    """Simula visualizações para gerar dados interessantes"""
    print("\n👀 Simulando visualizações...")

    # Padrão de visualizações (alguns posts mais populares)
    view_patterns = [50, 120, 80, 200, 45, 150, 30]  # views por post

    for post_id, views in enumerate(view_patterns, start=1):
        for _ in range(views):
            try:
                requests.get(f"{API_URL}/posts/{post_id}?increment_view=true")
            except:
                pass
        print(f"   ✓ Post {post_id}: {views} visualizações")


def main():
    print("🌱 Populando banco de dados com dados de exemplo\n")
    print("=" * 60)

    if not wait_for_api():
        return

    author_ids = seed_authors()

    if not author_ids:
        print("\n❌ Não foi possível criar autores. Abortando.")
        return

    seed_posts(author_ids)
    simulate_views()

    print("\n" + "=" * 60)
    print("✅ Dados inseridos com sucesso!")
    print("\n📊 Acesse a documentação da API: http://localhost:8000")
    print("🏆 Veja o ranking: http://localhost:8000/stats/top-posts")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
