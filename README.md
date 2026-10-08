# Demo base de chalé

Site de demonstração para hospedagens (chalés, pousadas): hero, história, cômodos, experiências,
galeria, comodidades, calendário de reservas e painel do proprietário. Os dados deste repositório
são genéricos. A cada prospect, só trocam textos e fotos; o layout é sempre o mesmo.

## Como gerar o site de um novo chalé

1. Use este repositório como template (ou copie a pasta) e dê o nome `demo-<nome-do-chale>`.
2. Apague as fotos de `fotos/` e coloque as do chalé (nomes curtos, sem acento: `quarto.jpg`, `hidro.jpg`).
3. Edite `chale.json`: textos, nome, cidade, comodidades e o nome das fotos (sem extensão).
4. Gere: `python3 build.py chale.json fotos .` (cria `index.html` e `img/`; o `sips` do macOS reduz as fotos).
5. Publique: GitHub Pages na branch `main`, pasta raiz.

## Regras do `chale.json`
- Obrigatórios: `slug, nome, cidade, uf, endereco, meta_desc, hero, galeria, comodidades, local, final`.
- Opcionais: `historia, numeros, comodos, experiencias, avaliacoes`. Sem dado real, apague a chave e a seção some do site e do menu.
- Nunca inventar nota, avaliações, depoimentos, preços ou história: só entra o que veio do anfitrião ou do anúncio.
- `*palavra*` num título vira destaque. Ícones de comodidade: bath, flame, snow, wifi, utensils, bed, coffee, car, paw, mountain, shield, home, wine, key, laptop.
- `tema` troca a paleta (ink, ink2, moss, cream, sand, amber, ember).
- `whatsapp` fica vazio na demo (o botão mostra um aviso). Só dígitos com 55 na versão vendida.
- Não remover o selo "Conceito de site — demonstração" nem o rodapé de demo.
