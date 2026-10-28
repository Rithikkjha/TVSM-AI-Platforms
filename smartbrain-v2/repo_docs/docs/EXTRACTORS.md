# Phase 2 extractors

Status: **implemented** for every stack present in the TVS-CS allowlist (java, node/express/nest,
react/nextjs, dotnet) plus the shared cross-stack extractors; angular is covered by the frontend
extractor. android, react-native, vue, python, ios, dart, flutter and php remain planned stubs: their
files stay `pending` (listed in `gaps.json` as `untouched_source` / `untouched_file`) for phase 3 and the stack is listed in
`state.phases.extract.missing_extractors`.
Item schema: [SCHEMAS.md#item-kinds-and-attributes](SCHEMAS.md#item-kinds-and-attributes).

## Contract (`repo_docs/extractors/base.py`)

```python
@dataclass(frozen=True)
class Evidence:
    file: str      # path relative to repo root (must be a ledgered, non-skipped file)
    line: int      # 1-based, <= ledger lines
    snippet: str   # the source line, trimmed, <=200 chars, redacted (config_classify + secrets.redact)

@dataclass
class InventoryItem:
    id: str                    # "<kind>:<subproject|.>:<kind key>", see SCHEMAS.md
    kind: str                  # INVENTORY_KINDS
    subproject: str
    attributes: dict           # every attribute key of the kind present; keys sorted on write
    evidence: list[Evidence]   # >=1, mandatory
    source: str = "code"       # "code" | "contract"
    extractor_id: str = ""     # serialized as "extractor": {"id": …, "version": …}
    extractor_version: str = ""
    confidence: str = "high"   # "high" | "medium"

@dataclass
class FileTouch:
    parse: str                 # "full" | "partial"
    error: str | None = None   # redacted parse error -> file stays pending

@dataclass
class ExtractResult:
    items: list[InventoryItem]
    touched: dict[str, FileTouch]   # every file the extractor opened because it was in scope

class Extractor(ABC):
    id: str                    # e.g. "java.spring"
    stacks: tuple[str, ...]    # meta stack ids it applies to ((), = shared: always applies)
    extractor_version: str     # bump => extract output stale for every repo it applies to
    status: str                # "implemented" | "planned"
    def applies_to(self, meta: dict, subproject: str | None = None) -> bool: ...
    # shared extractors (stacks == ()) run once per repo with subproject=None and attribute
    # items via ctx.subproject_of(file); stack extractors run once per (extractor, subproject)
    def extract(self, ctx: RepoContext, subproject: str) -> ExtractResult: ...
```
Source files are parsed with tree-sitter (`extractors/syntax.py`, grammar versions in `GRAMMAR_TAG` → part of
each source extractor's `extractor_version`); structured files with stdlib/PyYAML parsers (`extractors/configfmt.py`).
`RepoContext` gives read-only access to the clone, the ledger (non-skipped files of the subproject, in
path order), `meta`, the merged **config index** built by `shared.config` (run first, see order below)
and the external-systems registry. Extractors never write files; `repo_docs/phase2_extract.py`
(`PHASE_VERSION = "0.1.2"`) merges results, validates, writes `inventory.json` and `gaps.json`, updates the ledger and
the state.

Rules:
1. Every item carries evidence pointing at a real line of a ledgered, non-skipped file. The orchestrator
   re-reads the line, redacts it and requires the snippet to be a substring; violations fail the repo.
2. `touched[file].parse = "full"` only when the file was parsed by a real parser without errors and every
   construct of interest was resolved; otherwise `partial`. A clean tree with no construct of interest
   is `full` in every stack (nothing is unresolved). A file importing a client/driver package no rule
   covers (stack-specific lists, e.g. OpenSearch/NebulaGraph in java, kafkajs/amqplib in node) is
   `partial`. A file with any `full` touch → ledger `extracted`; the ledger `extractors[]` list records
   every touch (id, version, parse, items). **When in doubt, `partial`.** Under Option B phase 3
   revisits only what `gaps.json` lists (every `pending` file is listed, non-source ones as
   `untouched_file`), so an `extracted` file is
   never looked at again.
3. Never emit a secret value: every value goes through `config_classify` (SCHEMAS.md#config-value-classifier).
4. Deterministic: no wall-clock, randomness, absolute paths, or iteration over unordered sets;
   output sorted. A test runs each extractor twice over fixtures and compares bytes.
5. A file-level parse error is recorded in `inventory.errors[]` (level `file`) and never fails the repo;
   an extractor exception (bug) fails the repo (`extract: failed`, redacted error), other repos continue.
6. Items with the same `id` from several call sites/extractors are merged: evidence unioned, attributes
   merged (non-null wins; lists unioned). Precedence before a scalar conflict is declared: `source: code`
   beats `source: contract` (the contract only fills empty attributes; the code extractor is credited in
   `extractor`), and a `role: runtime` item beats a `tests_target` one with the same id. Inbound
   `responses` keep one entry per status (code entry first, empty fields filled from the contract).
   Remaining conflicts → `confidence: medium` and both values kept in a sorted list.

## Extractor ids

| id | applies to | module | finds |
|---|---|---|---|
| `shared.config` | always | `extractors/shared_config.py` | config files of every stack → `config_key`; builds the config index (key → per-env values/refs) |
| `shared.manifests` | always | `extractors/shared_manifests.py` | `pom.xml`, `build.gradle(.kts)`, `libs.versions.toml`, `*.csproj`, `Directory.Packages.props`, `packages.config`, `package.json` → `dependency`, `artifact` |
| `shared.infra` | always | `extractors/shared_infra.py` | Dockerfile, compose, k8s/helm, azure-pipelines, GitHub workflows, bicep/terraform → `infra` (+ Service Bus entities, CronJobs → `scheduled_job`) |
| `shared.contracts` | always | `extractors/shared_contracts.py` | OpenAPI/Swagger, Postman, proto, GraphQL, WSDL, AsyncAPI → `api_contract`, `inbound_http`/`schema` (`source: contract`), Postman in test suites → `outbound_http` (`role: tests_target`) |
| `shared.sql` | always | `extractors/shared_sql.py` | `*.sql` DDL/PLpgSQL, Flyway `V<n>__*.sql`, Liquibase changelogs → `data_access` (`owns_schema` in db-migration repos), stored procedures |
| `java.spring` | `java` | `extractors/java_spring.py` | Spring MVC/WebFlux/JAX-RS inbound, Bean Validation/Lombok schemas, RestTemplate/WebClient/RestClient/Feign/OkHttp/Apache/Retrofit outbound, Service Bus/JMS/Stream/Kafka/Rabbit messaging, JPA/Spring Data/JdbcTemplate/MyBatis/Mongo/MongoTemplate/OpenSearch/NebulaGraph/Redis data access, `@Value`/`@ConfigurationProperties`/`System.getenv` reads, `@Scheduled`/Quartz |
| `dotnet.aspnet` | `dotnet` | `extractors/dotnet_aspnet.py` | controllers/minimal APIs/Functions inbound, DataAnnotations/records schemas, HttpClient/IHttpClientFactory/Refit/RestSharp/Flurl outbound, ServiceBus*/MassTransit/Functions triggers, EF/Dapper/stored procs, `IConfiguration`/`IOptions<T>` reads, BackgroundService/Hangfire/Quartz/TimerTrigger |
| `node.backend` | `node`, `express`, `nest` | `extractors/node_backend.py` | Express/Nest inbound, class-validator/TS schemas, axios/fetch/got/HttpService outbound, `@azure/service-bus`/Nest transports/kafkajs/amqplib/bull messaging, TypeORM/Prisma/Sequelize/Mongoose/knex/pg/redis, `process.env`/`ConfigService.get`, node-cron/agenda/bull repeat |
| `node.frontend` | `react`, `nextjs`, `angular` | `extractors/node_frontend.py` | base URLs + API modules/wrappers → `frontend_api_call`; Next.js API routes/route handlers → `inbound_http`; TS request/response types → `schema` |
| `<stack>.planned` | android, react-native, vue, python, ios, dart, flutter, php | `extractors/stubs.py` | planned stub (`status: "planned"`, `extract` raises `NotImplementedError`) |

Order per repo: `shared.config` → `shared.manifests` → `shared.infra` → `shared.contracts` → `shared.sql`
→ stack extractors (alphabetical by id) → `repo_type` classification (needs all items) → external-system
matching. All extractors started at `extractor_version = "0.1.0"`; `node.*`, `dotnet.aspnet` and `shared.contracts` are at `0.1.1` after the phase-2 review fixes; `java.spring` is at `0.2.0`
(phase 3 part A: multi-hop wrappers, builder locals, MongoTemplate/OpenSearch/NebulaGraph, Service Bus
helper parameters; see its implementation notes) after `0.1.3`'s two run-and-verify fixes: a `${...}` placeholder assembled by constant concatenation
(`"${" + KAFKA_PREFIX + ".topics.booking}"`) is a config key, not a literal topic name; and publishes through the
tvsm-be-core wrapper `KafkaProducerUtil.send{String,Json,Bytes}[Sync|Async](topic, …)` are Kafka `publish` items.
Source extractors append the tree-sitter grammar tag, e.g. `0.1.3+ts0.26.0.java0.23.5`. The per-kind tables below describe the
target coverage; constructs a stack extractor does not handle yet are listed under "Left for phase 3"
in its implementation notes at the end of this file.

## inbound_http

**Route combination** (class/controller prefix + method template, then app-level prefixes):

| Framework | Rules |
|---|---|
| Spring MVC / WebFlux | class `@RequestMapping(value\|path)` + method `@Get/Post/Put/Patch/DeleteMapping` / `@RequestMapping(method=…)`; array values → one item each; then prefix `server.servlet.context-path`, `spring.mvc.servlet.path`, `spring.webflux.base-path` from `application*.yml/properties` (per env; the `default` profile value is used in `path`, all values kept in `context_path_by_env`, differing values → `medium`). Functional `RouterFunctions.route(GET("/x"), …)` → `medium` |
| JAX-RS | `@ApplicationPath` + class `@Path` + method `@Path` with `@GET/@POST…` |
| ASP.NET Core controllers | class `[Route("api/[controller]")]` with token replacement `[controller]` = class name minus `Controller`, `[action]` = method name, `[area]` = `[Area("x")]`; method `[HttpGet("{id}")]`/`[Route]`. A method template starting with `/` or `~/` is **absolute** and is not combined with the class prefix (`~/` stripped). Constraints/optionals `{id:int}`, `{id?}`, `{**slug}` → `{id}` with `type` from the constraint. Then `app.UsePathBase("/x")`. Conventional `MapControllerRoute` patterns are left for phase 3 |
| ASP.NET minimal APIs | `app.MapGet/MapPost/…("/x", …)`, `MapGroup("/prefix")` chains (one variable level) |
| Azure Functions | `[HttpTrigger(AuthorizationLevel.X, "get", "post", Route = "x/{id}")]` (default route = function name) prefixed by `host.json` `extensions.http.routePrefix` (default `api`); `AuthorizationLevel.Function/Admin` → `auth: api-key` |
| Nest | `@Controller('x')` (or `{path}`) + `@Get('y')`…; `app.setGlobalPrefix('api', {exclude: […]})` from `main.ts` (excluded routes skip the prefix); `enableVersioning({type: URI})` + `@Version('1')` → `/v1`; `RouterModule.register([{path, module}])` |
| Express | `app/router.<verb>('/x', …)`, `router.route('/x').get(…)`; mount prefixes from `app.use('/prefix', router)` followed across one `require`/`import` hop |
| Next.js API | `pages/api/**` and `app/**/route.(ts\|js)` exported `GET/POST/…`; file path → route, `[id]` → `{id}`, `[...slug]` → `{slug}`; `basePath` from `next.config.*` |

**Params:** path (template + `@PathVariable`, `[FromRoute]`, `@Param()`, `req.params.x`), query
(`@RequestParam`, `[FromQuery]`, `@Query()`, `req.query.x`), header (`@RequestHeader`, `[FromHeader]`,
`@Headers('x')`), body (`@RequestBody`, `[FromBody]`, implicit complex type with `[ApiController]`,
`@Body()`), form (`@RequestPart`, `[FromForm]`, `IFormFile`); `type` normalized, `required` from
`required=false`, C# `?`/default values, TS `?`, `@IsOptional`, `Optional<T>`.

**Request DTO:** the body parameter type, unwrapped (see [schema generics](#schema)).

**Responses:** Spring `ResponseEntity<T>` (status 200 unless `@ResponseStatus`), `@ResponseStatus(HttpStatus.CREATED)`,
springdoc/swagger `@ApiResponse(responseCode="404", content=@Content(schema=@Schema(implementation=X.class)))` /
`@ApiResponses`; ASP.NET `ActionResult<T>`, `Task<ActionResult<T>>`, `IActionResult` with
`[ProducesResponseType(typeof(X), StatusCodes.Status201Created)]` / `[ProducesResponseType(201)]`,
`Ok(x)`/`Created*(…)`/`NotFound()`/`BadRequest(x)` returns (`from: return`, `medium`); Nest
`@ApiResponse({status, type})`, `@ApiOkResponse/@ApiCreatedResponse…`, `@HttpCode(204)`, default 201 for
POST and 200 otherwise, return type `Promise<T>`/`Observable<T>`. Each response records `from`
(`return-type | annotation | return | default`).

**Auth:** ASP.NET `[Authorize]`, `[Authorize(Policy=…, Roles=…)]` on class/method, `[AllowAnonymous]`
overrides (`allow_anonymous: true`, `auth: none`), global `RequireAuthorization()`/fallback policy;
Spring `@PreAuthorize("hasRole('X')")`, `@Secured`, `@RolesAllowed`, `SecurityFilterChain`
`requestMatchers("/x").permitAll()/authenticated()` (path-matched → `medium`), `oauth2ResourceServer().jwt()`
→ `bearer-jwt`; Nest `@UseGuards(JwtAuthGuard)` class/method, global `APP_GUARD`, `@Public()`-style
metadata decorators that the guard skips (`medium`); Express middleware in the route chain or `app.use(auth)`
before the router (`medium`). `auth_raw` keeps the original expression.

## schema

Collected for every type referenced by an inbound/outbound/messaging item, transitively (nested types
listed as their own schema and referenced by name, cycles stopped by name).

| Language | Rules |
|---|---|
| Java | class/record fields (Lombok `@Data/@Value/@Getter/@Builder/@AllArgsConstructor` → private fields are the properties; without Lombok, getters); `@JsonProperty("x")` → `json_name`, `@JsonIgnore` excluded; Bean Validation `@NotNull/@NotBlank/@NotEmpty` (+ Lombok `@NonNull`) → `required: true`; `@Size(min,max)`, `@Min/@Max`, `@Pattern`, `@Email`, `@Positive`, `@Past/@Future`, `@Valid` (nested validated) → `validation`; enums with constants |
| .NET | class/record properties (positional record params included); `required` modifier, `[Required]`, non-nullable value types → required; `string?`/`Nullable<T>` → nullable; DataAnnotations `[StringLength]`, `[MaxLength]`, `[MinLength]`, `[Range]`, `[RegularExpression]`, `[EmailAddress]` → `validation`; `[JsonPropertyName]`/`[JsonProperty]`, `[JsonIgnore]`; enums with explicit values |
| TypeScript | classes with class-validator (`@IsString/@IsNumber/@IsNotEmpty/@IsOptional/@Length/@Matches/@IsEnum/@IsIn/@ValidateNested` + `@Type(() => X)`), Nest `@ApiProperty({required})`; interfaces and `type` aliases (`?:` → optional); TS `enum` and string-literal unions → `enum_values`; zod `z.object` (`medium`) |

**Type normalization:** primitives → `string | integer | number | boolean | date | datetime | uuid |
binary | object | any`; `enum[A,B]` for enums (template form). **Generics/wrappers:** transport
wrappers are unwrapped: `ResponseEntity<T>`, `ActionResult<T>`, `Task<T>`, `ValueTask<T>`,
`Task<ActionResult<T>>`, `Mono<T>`, `Optional<T>`, `CompletableFuture<T>`, `Promise<T>`, `Observable<T>`,
`AxiosResponse<T>`; collections become `T[]`: `List/Set/Collection/Iterable<T>`, `IEnumerable/ICollection/IList/IReadOnlyList<T>`,
`T[]`, `Array<T>`, `Flux<T>`; maps → `map<K,V>`; domain generics (`Page<T>`, `PagedResult<T>`,
`ApiResponse<T>`, custom `BaseResponse<T>`) become an instantiated schema (`Page<Booking>`) with type
parameters substituted into its fields. Types defined outside the repo (jar/NuGet/npm) → `resolved:
false`; phase 4 resolves those that live in a registered library repo.

## outbound_http

| Stack | Clients and base-URL sources |
|---|---|
| Java | `RestTemplate.getForObject/getForEntity/postForObject/postForEntity/exchange(url, HttpMethod.X, entity, T.class / ParameterizedTypeReference<T>)`; `WebClient.builder().baseUrl(…)` beans + `.get().uri("/x/{id}", …).retrieve().bodyToMono(T.class)`; `RestClient`; `@FeignClient(name, url="${svc.url}", path)` + interface `@*Mapping` methods (combined like inbound); `@HttpExchange` interfaces; OkHttp `Request.Builder().url(…)`; Apache `new HttpGet/HttpPost(url)`; Retrofit `@GET("x")` + `Retrofit.Builder().baseUrl(…)` |
| .NET | `HttpClient.GetAsync/PostAsync/PostAsJsonAsync/PutAsJsonAsync/DeleteAsync/SendAsync(new HttpRequestMessage(HttpMethod.X, url))`, `GetFromJsonAsync<T>`, `ReadFromJsonAsync<T>`; named `services.AddHttpClient("name", c => c.BaseAddress = new Uri(cfg["X"]))` + `IHttpClientFactory.CreateClient("name")`; typed `AddHttpClient<IFoo, Foo>(…)`; Refit `[Get("/x/{id}")]` + `AddRefitClient<T>().ConfigureHttpClient(…)`; RestSharp `new RestClient(baseUrl)` + `new RestRequest("x", Method.Post)`; Flurl `url.AppendPathSegment(…).PostJsonAsync(…)` |
| Node | `axios.get/post/…(url)`, `axios({method, url})`, `axios.create({baseURL})` instances (+ interceptors noted); `fetch(url, {method})`; `got`; Nest `HttpService` (`this.httpService.post(url)`) with `HttpModule.register({baseURL})` |

URL handling: literal, `config:<key>` (Spring `${x}`, `@Value` field, `IConfiguration["X"]`,
`IOptions<T>.Value.X`, `ConfigService.get('X')`) or `env:<VAR>` (`process.env.X`,
`Environment.GetEnvironmentVariable("X")`, `System.getenv("X")`); per-env non-secret values from the
config index go into `base_url_values`. String concatenation / template literals / `String.format` /
interpolated strings are normalized: `${id}`, `{0}`, `+ id +` → `{}` in `path_template`; query strings
are split into `query_params`. Request/response types from generic arguments, `T.class`, typed
`ReadFromJsonAsync<T>`, `axios.get<T>`, declared return types.

**Wrapper following — limit: one level (java.spring: up to 3 hops, multi-parameter URLs).** When a call site calls a function/method/bean in
the same repo whose body performs the HTTP call (e.g. `apiClient.get(path)` → `utils/api.ts` that calls
`axios.create({baseURL}).get(path)`, or a `BaseHttpService.post<T>(path, body)` helper), the
extractor resolves method, base URL and the path argument passed at the call site, records
`via_wrapper`, and sets `confidence: medium`. Not followed: wrappers calling other wrappers (depth ≥2),
URLs computed from runtime data (responses, DB rows), reflection/dynamic dispatch, and wrappers imported
from another repo/package. Those call sites leave the file `partial` and are phase 3's job (the ledger
shows which extractor touched the file). java.spring follows wrapper chains up to 3 hops in any class
(public `post(...)` → private `postMethodCall(...)` → `restTemplate.exchange(fullUrl, …)`) and substitutes
every parameter of the innermost URL (`baseUrl` + `endpoint`) at the call site; `via_wrapper` is the innermost
HTTP call and its line is added to the item's evidence. A parameter-derived URL beyond 3 hops leaves the file
`partial`.

## frontend_api_call

Repos: `TVS-CPS-PORTAL`, `cbs-admin-portal`, `location-frontend`, `Price-Engine-Frontend`, `qrcode-frontend`,
`master-data-platform-frontend`, `FormBuilder`, `TVS-CPS-FE-BASE-FRAMEWORK` (and any repo with react,
nextjs or angular stacks).

- **Base URLs:** `environment*.ts` (`environment.apiUrl`, per file env), `.env*` (`REACT_APP_*`, `VITE_*`,
  `NEXT_PUBLIC_*`, plus server-only vars for Next.js), `config.js` / `public/config.js` /
  `runtime-assets/**/config.json` (`window.__ENV__`-style runtime config), `next.config.*` (`env`,
  `publicRuntimeConfig`, `basePath`, `rewrites()` → recorded as proxy routes), `process.env.NEXT_PUBLIC_*`,
  `process.env.REACT_APP_*`, `import.meta.env.VITE_*`, constants modules (e.g. `src/constants/environment.constant.ts`),
  dev proxies (`setupProxy.js`, `proxy.conf.json`, vite `server.proxy`; `dev_only: true`).
- **Call sites:** API service modules (`src/services/**`, `src/api/**`, `utils/api.ts`), axios instances
  and fetch wrappers (one level, as above), Angular `HttpClient.get<T>(…)`, RTK Query
  `createApi({baseQuery: fetchBaseQuery({baseUrl})})` endpoints, SWR/React Query fetchers resolved through
  the wrapper rule.
- Output per call: method + `path_template` + `base_url_source`/values, request/response TS types,
  `runtime: browser|server`. Phase 4 turns them into `http` edges with `caller_type: frontend`, so
  "who calls X" includes the UIs.

## messaging

Azure Service Bus is the main broker in TVS-CS; every `events.publishes[]` / `events.subscribes[]`
template field has an attribute (SCHEMAS.md).

| Stack | Publishers | Consumers |
|---|---|---|
| Java | `azure-messaging-servicebus`: `ServiceBusClientBuilder().sender().topicName(X)/queueName(X)`, `ServiceBusSenderClient.sendMessage(s)`; spring-cloud-azure `ServiceBusTemplate.send("x", msg)`; JMS `JmsTemplate.convertAndSend("x", …)`; Spring Cloud Stream `StreamBridge.send("binding", …)` + `spring.cloud.stream.bindings.<fn>-out-0.destination`; `KafkaTemplate.send("t", …)`; tvsm-be-core `KafkaProducerUtil.sendJson/sendString/sendBytes[Sync|Async]("t", …)`; `RabbitTemplate.convertAndSend(exchange, routingKey, …)` | `ServiceBusClientBuilder().processor().topicName(X).subscriptionName(Y).processMessage(h)`, `.receiver()`; `@ServiceBusListener(destination="${x}", group="${sub}")`; `@JmsListener(destination, subscription, containerFactory)`; Stream `Consumer<…>` beans + `…-in-0.destination/group`; `@KafkaListener(topics, groupId)`; `@RabbitListener(queues)` |
| .NET | `ServiceBusClient.CreateSender("x")` + `SendMessage(s)Async`; MassTransit `IPublishEndpoint.Publish<T>` / `ISendEndpointProvider` (entity name by MassTransit convention → `medium`); `EventGridPublisherClient`, `EventHubProducerClient`, `QueueClient.SendMessageAsync` | `CreateProcessor("topic", "sub", options)` / `CreateSessionProcessor` + `ProcessMessageAsync += H`; Functions `[ServiceBusTrigger("%Topic%", "%Sub%", Connection = "SB")]` (`%X%` resolved through `local.settings.json`/app settings → `name_from: config:X`), `[EventGridTrigger]`, `[EventHubTrigger]`, `[QueueTrigger]`; MassTransit `ReceiveEndpoint("q", e => e.Consumer<T>())`, `SubscriptionEndpoint<T>("sub", "topic")` |
| Node | `@azure/service-bus` `client.createSender("x").sendMessages({body, subject, applicationProperties, sessionId, correlationId})`; Nest `ClientProxy.emit('pattern')` / `send`; kafkajs `producer.send({topic})`; amqplib `publish/sendToQueue`; bull `queue.add` | `createReceiver("topic", "sub")` / `createReceiver("queue")` + `subscribe({processMessage, processError})`; Nest microservice transports (`Transport.*`, custom Service Bus strategies) with `@MessagePattern('x')`/`@EventPattern('x')`; kafkajs `consumer.subscribe({topic})`; amqplib `consume`; bull `@Processor('x')`/`queue.process`; Redis `subscribe` |

- **Entity name resolution through config:** a literal is used directly; otherwise record `name_from`
  (`config:<key>` / `env:<VAR>`), `name_key`, and `resolved_values{<env>: <name>}` for every env file that
  defines it (names are non-secret, rule 5). `entity` = the `default` env value, else the single value, else
  `null` (`medium`).
- **Namespace:** `spring.cloud.azure.servicebus.namespace`, `fullyQualifiedNamespace`, `ServiceBusClient("<ns>.servicebus.windows.net", credential)`,
  or the `Endpoint=sb://<ns>…` host parsed from a connection string (never the key).
- **Message details:** `subject`/`setSubject`/`Subject =`, `applicationProperties["type"|"eventType"|"messageType"]`
  literals → `message_types`; `sessionId`/`setSessionId`, `correlationId`, `partitionKey` → `properties`;
  payload type from the serialized object / generic argument. Java: publish → the declared type of `x`
  in `new ServiceBusMessage(<serializer>(x))` (`toJson`, `writeValueAsString`, `BinaryData.fromObject`, …)
  in the linked sender class, or the last argument of `JmsTemplate`/`ServiceBusTemplate`/`KafkaTemplate`/
  `RabbitTemplate`/`StreamBridge` sends; subscribe (listener annotations) → `T` of
  `readValue(…, T.class)` in the handler, else the first non-envelope parameter type. The payload type
  is also emitted as a `schema`. Unresolved payloads are listed in `gaps.json` (`missing_payload`).
- **Error handling:** `MaxDeliveryCount`/`max_delivery_count` (admin client, bicep `Microsoft.ServiceBus/namespaces/topics/subscriptions`,
  terraform `azurerm_servicebus_subscription`), `deadLetterMessage(`/`DeadLetterMessageAsync(`, `dead_lettering_on_message_expiration`,
  `ServiceBusRetryOptions`/`AmqpRetryOptions`/`spring.cloud.azure.servicebus.retry.*` → `error_handling`.
- Subscription rules/filters (`CreateRuleAsync`, `SqlRuleFilter`, `CorrelationRuleFilter`, IaC rules) → `filter`.

## data_access

- **Java:** JPA `@Entity` + `@Table(name, schema)`, Spring Data `extends JpaRepository/CrudRepository/MongoRepository<T, ID>`
  (derived `find*/get*/count*/exists*` → read, `save*/delete*` and `@Modifying @Query` → write; repository
  used only through read methods → `read`, else `both`), `@Query(nativeQuery = true)` SQL, `JdbcTemplate`/`NamedParameterJdbcTemplate`
  SQL literals, MyBatis mapper XML/annotations, `@Procedure`/`SimpleJdbcCall.withProcedureName`, `@Document(collection)`,
  `RedisTemplate`/`StringRedisTemplate` key prefixes (`medium`).
- **.NET:** `DbContext` + `DbSet<T>`, `[Table("x", Schema = "y")]`, fluent `ToTable(…)`; `UseSqlServer/UseNpgsql(cfg.GetConnectionString("X"))`
  → `name_from: config:ConnectionStrings:X`; Dapper `Query/Execute("SQL")`; `CommandType.StoredProcedure`,
  `EXEC sp_x`, `FromSqlRaw("EXEC …")` → `stored_procedures`; Cosmos `GetContainer("db", "c")`, `BlobContainerClient("c")`.
- **Node:** TypeORM `@Entity('x')` + `getRepository/Repository<T>`, Prisma `schema.prisma` models (`@@map`),
  Sequelize `define('x')`/`tableName`, Mongoose `model('X', schema, 'collection')`, knex `knex('t')`, `pg`/`mysql2` `query('SQL')`,
  `ioredis`/`redis` clients.
- SQL literals: tables from `FROM/JOIN/INTO/UPDATE/DELETE FROM/MERGE INTO` (`medium`); operation from the verb.
- **Store identity:** `store_type`, `host`, `database` parsed from connection strings/JDBC URLs/config
  (classifier rule 4 never lets the string itself through). Unknown host → `_`.
- **db-migration (`TVS-CPS-DB-MIGRATION`, PostgreSQL):** `shared.sql` parses `CREATE/ALTER TABLE`, `CREATE VIEW`,
  `CREATE [OR REPLACE] FUNCTION/PROCEDURE … LANGUAGE plpgsql` → one `data_access` item with `owns_schema: true`,
  `tables_ddl[]` and `routines[]`. Phase 4 links the TVS-CPS family's tables to it (`owns_schema` edges,
  `owned: false, owner_service: tvs-cps-db-migration` in the consumers' `data_stores`).

## config

Every key **read** in code and every key **defined** in a config file becomes one `config_key` item.

- Reads: `IConfiguration["X"]`, `GetValue<T>("X")`, `GetSection("X")` (+ bound `IOptions<T>`/`Configure<T>(GetSection("X"))`
  properties as `X:Prop`), `GetConnectionString("X")`, `@Value("${x.y:default}")`, `@ConfigurationProperties(prefix)` class fields,
  `Environment.getenv/System.getenv/Environment.GetEnvironmentVariable`, `process.env.X`, `ConfigService.get('X')`,
  `import.meta.env.X`.
- Definitions: `appsettings*.json`, `local.settings.json`, `web.config` `appSettings`/`connectionStrings` (names only for the latter),
  `application*.yml/properties` (incl. multi-document profiles), `bootstrap*.yml`, `.env*` (`.env.example` values are
  sample values: name + `required` only), `environment*.ts`, `config.js`, k8s ConfigMap/env, helm values, pipeline variables.
- **Key normalization (`canonical`):** lowercase; `:` and `__` → `.`; Spring relaxed binding drops `-`
  and case inside a segment (`booking.base-url` = `booking.baseUrl` → `booking.baseurl`); env-style `A_B_C`
  → `a.b.c`. Env↔property joins that need the underscore rule are `medium`.
- Values per env only through the [classifier](SCHEMAS.md#config-value-classifier): URL/host/path/topic/
  queue/entity/db-name-like non-secret values are recorded; secret-like keys or values → name only +
  `secret: true`; Key Vault references → `kv_ref` only.

## scheduled_job

`@Scheduled(cron|fixedRate|fixedDelay = "${x}")` (+ `zone`), Quartz `CronScheduleBuilder`/`JobBuilder`/`quartz.*` config,
Hangfire `RecurringJob.AddOrUpdate(…, Cron.X / "expr")`, `BackgroundService`/`IHostedService` (+ `PeriodicTimer`/`Task.Delay`
interval, `medium`), Functions `[TimerTrigger("%Schedule%")]`, `node-cron` `cron.schedule("expr")`, `@nestjs/schedule`
`@Cron(...)`/`@Interval`, agenda `every(...)`, bull `{repeat: {cron}}`, k8s `CronJob.spec.schedule`. Expressions resolved
through config like entity names.

## external_systems

After all items exist, hosts of `outbound_http`/`frontend_api_call` base URLs and of URL-valued `config_key`
items, dependency names and SDK
symbols are matched against `registry/external_systems.yaml` (SCHEMAS.md#registryexternal_systemsyaml).
A hit emits one `external_system` item per (system, subproject) (`extractor: external_systems@0.1.0`, the
orchestrator's matcher in `repo_docs/external_systems.py`) and sets the call's `target_hint: external:<name>`. Unmatched
third-party hosts are left for phase 4, which lists them in `registry/external_candidates.json`; to extend
the registry add an entry there and re-run `extract` + `resolve`.

## dependencies / build

`pom.xml` (direct `<dependencies>`, `<parent>` as `kind: parent`, `<modules>` as `kind: module`,
`<dependencyManagement>` BOM imports, `${prop}` versions resolved from `<properties>` in the same repo,
own `groupId:artifactId` → `artifact`), `build.gradle(.kts)` (`implementation/api/compileOnly/testImplementation 'g:a:v'`,
`libs.versions.toml` catalogs), `*.csproj` (`PackageReference`, `ProjectReference` as `project-reference`,
`PackageId`/`IsPackable` → `artifact`), `Directory.Packages.props`, `packages.config`, `package.json`
(`dependencies/devDependencies/peerDependencies/optionalDependencies`, `workspaces`, own `name`/`version`
→ `artifact`, `github:`/git URLs). Lock files are not read (skipped in the ledger). `internal: true` when
the name matches `internal_package_patterns` (planned org key; not set for TVS-CS) or is an artifact/module of the
**same** repo (`internal_repo` = this repo). Phase 2 extracts one repo at a time, so a dependency on another repo's
artifact (e.g. `com.tvsm:tvsm-be-core` from `TVS-CPS-BE-BASE-FRAMEWORK`) stays `internal: false` here; phase 4
matches dependencies against every repo's `artifact` items and turns matches into `library_dependency` edges.

## infra / deploy

Dockerfile (`FROM` base images per stage, `EXPOSE`, `ENV`/`ARG` names + classified values, `ENTRYPOINT/CMD`),
docker-compose services (name, image, ports, env, depends_on), k8s/helm (`Deployment`/`Service`/`Ingress`/
`ConfigMap`/`CronJob`/`HorizontalPodAutoscaler`; service names + namespace, ports, ingress `hosts` and
`paths → backend service`, container env with `configMapKeyRef`/`secretKeyRef` names, image; helm
`values*.yaml` image/ingress/env, Go-templated manifests → `partial`), azure-pipelines (variables names +
classified values, `group:` variable groups, `environment:`, deploy tasks' AKS/App Service/Function App names,
service connection names), GitHub workflows (`env`, `environment`, `secrets.X` names only), bicep/terraform
Service Bus namespaces/topics/subscriptions/queues. These feed phase 4's host → service index.

## api_contracts

OpenAPI 2/3 (JSON/YAML), Postman collections, `.proto` (services/rpcs → `inbound_http`-like items with
`framework: grpc`), GraphQL SDL (`Query`/`Mutation` fields), WSDL operations, AsyncAPI channels (→ `messaging`),
all with `source: contract` and `contract_file`. Generated-spec detection: Swashbuckle (`AddSwaggerGen`/`UseSwagger`,
`Swashbuckle.AspNetCore` package → `docs_path: /swagger/v1/swagger.json`), springdoc (`springdoc-openapi-*`,
`springdoc.api-docs.path`, default `/v3/api-docs`), `@nestjs/swagger` `SwaggerModule.setup('path')` →
`api_contract` with `generated: true`. Contract routes carry `handler: null` (an `operationId` is not a
code handler). When code and contract describe the same route, the code item wins and the contract fills
missing fields (rule 6).

## repo_type classification

Module `repo_docs/repo_type.py`; ordered rules, first match wins, every fired rule recorded with evidence in
`meta.repo_type` (also per subproject):

| # | value | rule | TVS-CS examples |
|---|---|---|---|
| 1 | `db-migration` | ≥50% of non-skipped source files are SQL migrations (Flyway/Liquibase layout or `*.sql` DDL) and no `inbound_http` | `TVS-CPS-DB-MIGRATION` |
| 2 | `test-suite` | test-framework deps (testng, rest-assured, karate, cucumber, selenium, playwright, cypress) and no runnable app entrypoint, or ≥50% of non-skipped files are `test`; its `outbound_http` items get `role: tests_target` | `Core-Commerce-Platform-API-Service-Testng`, `Lead-Booking-Crud-Services-Testing` |
| 3 | `library` | no app entrypoint (`@SpringBootApplication` main, `WebApplication`/`Host` builder, `NestFactory.create`, `app.listen`, Next/React app) and publishes an `artifact` (jar without boot repackage, `IsPackable`, npm `main`/`exports`) | `TVS-CPS-BE-BASE-FRAMEWORK`, `TVS-CPS-FE-BASE-FRAMEWORK` |
| 4 | `function-app` | Azure Functions worker/host (`host.json`, `Microsoft.Azure.Functions.Worker`, `[Function]`) | – |
| 5 | `mobile` | android, ios, react-native, dart/flutter stacks | – |
| 6 | `frontend` | react/nextjs/angular/vue stack with UI routes and no backend inbound beyond Next API routes | `TVS-CPS-PORTAL`, `location-frontend`, … |
| 7 | `scheduler` | `scheduled_job` items and no `inbound_http` / subscribe | candidate: `Catalog-Scheduler` |
| 8 | `service` | any `inbound_http` or messaging `subscribe` | most backends |
| 9 | `unknown` | none of the above (reported in `status`) | – |

`template_type`: service → `backend-api` (`bff` when the name contains `bff`/`backend-for-frontend`),
frontend → `frontend-web` (`portal` when the name contains `portal`), function-app → `function`,
scheduler → `worker`, library → `library`, mobile → `mobile-app`; `test-suite`, `db-migration`,
`unknown` → `null` (no template value yet; phase 5 open item).

## Observed TVS-CS stacks (phase 0/1 run, 42 cloned allowlisted repos)

java 22 repos (Maven, Spring Boot 3.5.x, `starter-web` 18, `webflux` 5, `data-jpa` 14, `data-mongodb` 3,
`spring-kafka` 3, `spring-cloud-azure` 4; TVS-CPS-BACKEND is a 15-module monorepo) · node 16 (express 5,
react 5, nextjs 3 on Next 15/React 19, nest 3 on Nest 10–11; axios everywhere; `@azure/service-bus` in 5;
mongoose/typeorm/prisma) · dotnet 4 (ASP.NET Core net9.0 ×14 projects, net8 ×2, net7 ×1; EF Core SqlServer,
Swashbuckle, RestSharp, Azure Functions + Service Bus). No angular, python, php, dart/flutter, ios or android.
Build order used: shared → java.spring → node.backend → node.frontend → dotnet.aspnet.

## java.spring implementation notes

Modules: `java_symbols.py` (repo-wide index: packages, imports incl. static/wildcard, nested types,
constants, `@Value` fields/params, constructor-injected fields + `@Qualifier`, `@ConfigurationProperties`,
`@Bean` methods; `resolve_expr` → `ValueSource literal|config|env|param|unknown`), `java_inbound.py`,
`java_http.py`, `java_messaging.py`, `java_data.py`, `java_types.py`, orchestrated by `java_spring.py`
(`extractor_version = 0.2.0+<GRAMMAR_TAG java part>`). Rules beyond the tables above:

- `${...}` placeholders are recognised after constant folding, so `"${" + KAFKA_PREFIX + ".topics.order}"`
  is `config:<prefix>.topics.order`; `@Value(Constants.PROP)` fields resolve through the constant the same way
  (value resolution only: `config_key` read items still come from literal `@Value("${…}")` text).
- Messaging helpers that build a Service Bus client from their parameters (notification-dispatcher-service
  `createServiceBusProcessorClient(conn, topicName, subscriptionName, exec)`) are re-emitted once per call
  site in the same class (one hop, same arity, bare / `this.` receiver), resolved in the caller's scope
  (`@Value` bean parameters); call sites sharing a topic merge into one item and differing subscriptions
  become a sorted list (`medium`). A helper without call sites keeps `name_from: unknown`.
- Same-class helpers **with arguments** are inlined (`buildSafeUrl(baseUrl, endpoint)`): the single return
  expression is resolved in the helper's scope and each of its parameter segments is replaced by the
  caller's argument. `UriComponentsBuilder` chains are followed through typed locals / helper results
  (`builder.build().toUriString()`); `path(param)` inserts the `/` separator; `URI.create(x)` is `x`.
- WebClient / RestClient base: a builder held in a local (`WebClient.Builder b = WebClient.builder()
  .baseUrl(x)…; return b.build()`) and `buildClient(...).mutate()….build()` keep the builder's `baseUrl`
  (a later `baseUrl` wins). A builder chain **without** `baseUrl` means "no base": `uri(x)` is the whole
  URL. `uri(x)` also replaces the base when `x` is an absolute literal, the base's own key, or a config key
  whose value is `http(s)://…`. A client parameter shadowing a same-named field binds through its
  `@Qualifier` / name to a `@Bean` of the same type, else the repo's only `@Bean` of that type. A field set
  by a Lombok `@RequiredArgsConstructor` / `@AllArgsConstructor` constructor binds to the arguments of the
  single `@Bean` method calling `new <Type>(…)` with that arity (also used for the declared type of a
  properties field, so an abstract `CatalogueApiProperties` field resolves the subclass prefix).
  Static `ParameterizedTypeReference<X>` constants give the response type `X`.
- MongoTemplate / ReactiveMongoTemplate / MongoOperations calls: op from the method name (`find*`,
  `count`, `exists`, `aggregate*`, `stream` → read; `insert*`, `save`, `update*`, `upsert`, `remove`,
  `findAndModify`, `bulkOps`, … → write); entity = an in-repo `X.class` argument (its `@Document`
  collection joins `collections`), collection = a resolved literal argument. Other methods or calls with
  neither leave the file `partial`. `orm: mongo-template` unless repositories exist (`spring-data`).
- OpenSearch (`store_type: opensearch`, `orm: opensearch-client`): `.index(name)` on a request-builder
  lambda parameter or a `*Request.Builder` local in types holding an `OpenSearchClient` (fields incl.
  supertypes, or a parameter); op from the enclosing client call (`search`, `scroll`, `get`, `exists` → read;
  `index`, `bulk`, `delete`, `update`, `refresh`, … → write), else the method's client calls. Wrapper methods
  taking the index name as a parameter are followed (up to 5 rounds, e.g. `execute/4 → /5 → /6`). One entity row per
  index; `name_from` = the properties class' `host`/`hosts`/`uris` key (host only from config values).
  An index name that cannot be resolved leaves the file `partial` (the store keeps its evidence).
- NebulaGraph (`store_type: nebula`, `orm: nebula-client`, `medium`): `Session` / `SessionPool` /
  `NebulaPool` `execute*(stmt)` in files importing `com.vesoft.nebula`, plus repo methods passing their
  parameter on (wrappers, followed like OpenSearch). The statement text gives the op (`MATCH`/`FETCH`/
  `GO`/`LOOKUP`/… read, `INSERT`/`UPSERT`/`UPDATE`/`DELETE` write) and tag/edge names (`:tag`, `ON tag`,
  `VERTEX`/`EDGE`); `USE <space>` and `new SessionPoolConfig(addrs, space, …)` give `database`. Statements
  that do not start with literal text, or with a runtime tag (`MATCH (v:%s)` with a parameter), leave the
  file `partial`.
- Store object names (OpenSearch index, Nebula space) do not go through classifier rule 5 (it hides
  `*Index`/`space` keys): a value is recorded when no key in the chain is secret-like, the value is not
  secret-like and it is name-shaped (`[A-Za-z0-9._-]{1,128}`). Config values first; when the key is defined
  nowhere in the repo, the `@ConfigurationProperties` field's literal initializer of **that** property is
  used under pseudo-env `code-default` (`medium`). Other fields' defaults (e.g. a password) are never read.
- A `@Bean` returning `OpenSearchClient` / `SessionPool` / `NebulaPool` / `MongoClient` / `MongoTemplate`
  adds its line to the evidence of that store in the same subproject.
- Files that mention an HTTP client but have no call site and whose every type is a client factory
  (`@Configuration` with a `@Bean` returning a client), client holder (constructors/getters only), interface
  or client interceptor are recorded in `ctx.hints["silent_ok"]`; gaps.json does not list them as
  `silent_client_file` and counts them in `summary.suppressed`.

- Context path comes only from config files of the **same subproject**; `context_path_by_env` lists every
  env with a value (default fallback per env).
- Service Bus sender beans are linked to `sendMessage(s)` call sites through `@Qualifier` / field names
  (`published_by` = first send site; `ServiceBusMessage` setters in that class → `message_types`/`properties`).
- `SecurityFilterChain`: `requestMatchers(...)` rules matched against the route without context path;
  `authenticated()` → `bearer-jwt` when `oauth2ResourceServer`/`jwt` or a JWT/token filter is added
  (`addFilterBefore(jwt…)`), else `basic`/`unknown`; always `medium`. Non-literal matcher arguments
  (`OPEN_URLS.toArray(...)`) leave the file `partial`.
- `scheduled_job.resolved_values`: cron/number-shaped schedule values are recorded when neither the key
  chain nor the value is secret-like (the classifier would otherwise hide them as rule 6).
- Spring Data operation rollup: call sites on repository-typed fields first, else the repository's
  declared methods (`@Modifying` → write).
- Left for phase 3 (file `partial`): Retrofit, functional `RouterFunctions`, `java.net.http` /
  `HttpURLConnection`, MyBatis, Elasticsearch/Cosmos/Blob clients, Event Hubs SDK clients,
  `ServiceBusAdministrationClient`, WebSocket/gRPC, wrappers deeper than 3 hops, entity
  names computed at runtime (e.g. notification-service `queueName(queueName)` cache loader), env-var topic
  names with no value in the repo, unannotated Spring handler parameters, payloads of processor-chain
  (`processMessage`) consumers, OkHttp `newCall(request)` with the `Request` built elsewhere,
  `EntityManager` custom repositories, `StringBuilder.append` URL building, ternary URLs, Nebula
  statements built by helpers in other classes. Besides the type-name denylist, importing any client/driver
  package without a rule (`UNSUPPORTED_IMPORTS`: `org.elasticsearch`, `com.azure.cosmos`, `com.mongodb`,
  `software.amazon.awssdk`, `io.grpc`, …) leaves the file `partial`.
- Mockito/BDDMockito stubs (`when(client.get())`, `verify(...)`, `given(...)`) are not call sites.
- SQL store identity: `spring.datasource.url` / `jdbc-url` / `spring.r2dbc.url` in the subproject; when
  none is defined there, the single `*.datasource[.*].url` property anywhere in the repo (e.g.
  TVS-CPS-BACKEND `tvsm.core.multitenant.datasource.default-data-source.url` in `tvs-cps-app`) → `name_from:
  config:<key>` + host/database; ambiguous → no identity.
- SDK symbols: declared top-level type names (java, .NET) and imported names / declared classes (node)
  matching a registry `sdk_symbols` pattern feed `ctx.hints["sdk_symbols"]` (`RepoContext.note_sdk_symbol`).

## node.backend / node.frontend implementation notes

Shared module `node_common.py` (module graph with tsconfig/jsconfig `baseUrl` + `paths` aliases, ES/CJS
imports and re-exports, abstract evaluator, HTTP model, config reads, TS schemas). Both extractors use
`extractor_version = 0.1.1+<GRAMMAR_TAG ts/tsx/js part>` and share caches in `ctx.symbols['node']` /
`ctx.symbols['node.http']`, so each file is parsed once per repo. `node.backend` applies to `express`,
`nest`, or plain `node` subprojects without `react`/`nextjs`/`angular`; `node.frontend` to `react`,
`nextjs`, `angular`. Rules beyond the tables above:

- Test files (ledger class `test`, `__tests__/`, `test/`, `mocks/`, `.spec`/`.test`) are not opened: they
  only mock clients. Every other source file of the subproject (+ its tsconfig, `schema.prisma`) is
  touched; `full` for clean trees with nothing unresolved (also when the file has no construct of
  interest), `partial` for files importing a package from `node_common.UNSUPPORTED_PKGS` (kafkajs,
  amqplib, bull/bullmq, RTK Query, SWR/React Query, OpenSearch/Elastic, Cosmos/Blob, gRPC, websockets, …).
- Unmounted Express routers → prefix `''`, `medium`, file `partial`. Azure Functions v4 `app.http` use
  `host.json` `routePrefix` (default `api`); Next.js `basePath` from an env var → `context_path_by_env`.
- Wrappers: the innermost function owning the URL's leading parameter (object-literal methods, class
  methods/arrow fields with `export default new X()`, exported functions, factory closures such as
  `createHttpService(baseURL)`), plus one `axios.create` factory hop.
- `process.env.X || 'http://…'` literal fallbacks → pseudo-env `code-default` in `base_url_values`.
- Service Bus entity names: literal, `process.env`, `ConfigService.get` → `config:<key>`, or one
  constructor/method parameter hop; names destructured from a JSON secret → `name_from: unknown` +
  `name_key` (key `…:unknown:<name_key>`); `subscription` keeps the reference when unresolved. Nest
  `@EventPattern`/`@MessagePattern` without a known transport → `broker: null`.
- Config reads record names and read sites only (`secret` null/true), so they merge with `shared.config`
  without conflicts.
- Left for phase 3 (file `partial` or not detected): kafkajs, amqplib, bull queues, knex, RTK Query
  `createApi`, SWR/React Query fetchers beyond the wrapper rule, `next.config` `rewrites()`/`env`,
  `setupProxy.js` / vite `server.proxy`, `sendMessages` `subject`/`applicationProperties` →
  `message_types`, Express response status codes, wrappers of wrappers (e.g. TVS-CPS-FE-BASE per-call
  `{baseURL}` override).

## dotnet.aspnet implementation notes

Modules: `dotnet_symbols.py` (repo-wide C# index in `ctx.symbols['csharp']`: types, constants, named/typed
`AddHttpClient` and `AddRefitClient` base addresses, `Configure<T>(GetSection)` option sections,
DbContexts, `[Table]`/`ToTable` names, default auth scheme; resolver for literals, interpolation, `??`,
`IConfiguration["A:B"]`, `GetSection(..)[..]`, `GetValue<T>`, `GetConnectionString`, `IOptions<T>.Value.P`,
`Environment.GetEnvironmentVariable`, `nameof`, `string.Format`, one hop through locals/fields/ctor
assignment, depth 8), `dotnet_types.py` (type normalization, wrapper unwrapping), orchestrated by
`dotnet_aspnet.py` (`extractor_version = 0.1.1+<GRAMMAR_TAG csharp part>`). Rules beyond the tables above:

- Responses: annotations (`[ProducesResponseType]`/`[SwaggerResponse]`, `StatusCodes.StatusNNN`,
  `HttpStatusCode` names) + return type + `return Ok/Created/NotFound/…` statuses not already covered
  (`from: return`); the item is `medium` only when every response came from returns.
- `[FromBody] object|string|JObject` with exactly one `JsonConvert.DeserializeObject<T>` in the action →
  `request: T`, `medium`. Unattributed params: route token → path, simple type → query, complex → body
  (with `[ApiController]`).
- Schedules (`TimerTrigger %X%`, Quartz) are recorded only when key and value are not secret-like and the
  value is cron/TimeSpan-shaped.
- Wrappers: one level, same file. Data access items for the same store merge within a run (`ef-core` wins
  over ado/dapper); `FromSqlRaw`/`ExecuteSqlRaw("EXEC sp")` attach to the subproject's single ef-core
  store, else the file is `partial`.
- Test-project `.cs` files: only `outbound_http` with `role: tests_target`, always `partial`.
- Left for phase 3: conventional `MapControllerRoute` routes, routes inherited from base controllers,
  domain generic instantiation, wrappers at depth ≥2 or cross-file, dynamic env var names
  (`GetEnvironmentVariable(obj.prop)`), dynamic Service Bus entity names (`CreateSender(queueName)` →
  `name_from: unknown`, `medium`).
