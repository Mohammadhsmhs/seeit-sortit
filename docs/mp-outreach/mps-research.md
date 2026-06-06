# London MPs — Research Findings

Researched 2026-06-02. London has **74 parliamentary constituencies** (post-July 2024 boundary review — verified against UK Parliament API).

## Key Facts
- **74 London MPs** (fetched live from Parliament API into `london_mps.json`)
- **Party split** (verified, June 2026):
  - Labour: 47
  - Labour (Co-op): 10
  - Conservative: 8
  - Liberal Democrat: 6
  - Independent: 2
  - Reform UK: 1
- **12 constituencies span multiple boroughs** — boroughs and constituencies don't map 1:1.
- **Twitter coverage**: 61 of 74 MPs have a public X/Twitter handle in the API.

## Programmatic Data Sources

### UK Parliament Members API (no auth required)
| Use case | Endpoint |
|----------|----------|
| All current Commons MPs | `GET /api/Members/Search?House=Commons&IsCurrentMember=true&skip=0&take=20` (paginate) |
| Single constituency | `GET /api/Location/Constituency/{id}` |
| **Postcode → MP** (routing primitive) | `GET /api/Location/Constituency/Search?searchText={postcode}` |
| Member contact (email, Twitter) | `GET /api/Members/{id}/Contact` |
| OpenAPI spec | https://members-api.parliament.uk/index.html |

### ONS Open Geography Portal — constituency ↔ borough mapping
- **PCON25 to LAD24 lookup**: gives one "dominant" borough per constituency
- **Postcode to PCON July 2024 lookup**: one row per UK postcode → constituency
- For 12 multi-borough constituencies: use ONS Output Area (OA21) → PCON → LAD lookup and aggregate

Search the portal: https://geoportal.statistics.gov.uk/search?collection=Dataset&tags=parliamentary+constituencies

## Email Format
- **Default**: `firstname.lastname.mp@parliament.uk`
- **Caveat**: a handful of MPs publish a constituency-office address instead. Always call `/Members/{id}/Contact` to confirm before bulk-sending.

## Multi-borough constituencies (post-2024)
These cross borough boundaries — need special handling in routing:
- Beckenham and Penge
- Eltham and Chislehurst
- Erith and Thamesmead
- Dulwich and West Norwood
- Southgate and Wood Green
- Stratford and Bow
- Streatham and Croydon North
- Vauxhall and Camberwell Green
- Cities of London and Westminster
- Chingford and Woodford Green
- (+2 more)
