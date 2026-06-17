# API do Phonebook App

URL local: `http://localhost:3001`

## Verificar saúde

```bash
curl http://localhost:3001/api/health
```

Resposta:

```json
{
  "status": "ok"
}
```

## Listar contatos

```bash
curl http://localhost:3001/api/contacts
```

## Criar contato

```bash
curl -X POST http://localhost:3001/api/contacts \
  -H "Content-Type: application/json" \
  -d '{"name":"Maria Silva","phone":"(11) 99999-9999"}'
```

## Atualizar contato

```bash
curl -X PUT http://localhost:3001/api/contacts/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Maria Souza","phone":"(11) 98888-8888"}'
```

## Excluir contato

```bash
curl -X DELETE http://localhost:3001/api/contacts/1
```

## Enviar feedback

```bash
curl -X POST http://localhost:3001/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@example.com","message":"Aplicativo muito útil!"}'
```

Para feedback anônimo, omita o e-mail ou envie `null`:

```bash
curl -X POST http://localhost:3001/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"email":null,"message":"Sugestão de melhoria: adicionar filtros avançados."}'
```

## Validações

### Contatos

- `name`: obrigatório, entre 2 e 80 caracteres
- `phone`: obrigatório, entre 8 e 20 caracteres
- O telefone aceita números, espaços e os caracteres `+`, `(`, `)`, `-`

### Feedback

- `email`: opcional, até 100 caracteres, deve ser um e-mail válido
- `message`: obrigatório, entre 10 e 500 caracteres

Erros de validação retornam HTTP `400`:

```json
{
  "error": "Informe um telefone válido com 8 a 20 caracteres."
}
```
