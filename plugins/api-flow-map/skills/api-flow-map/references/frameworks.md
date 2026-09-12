# Framework coverage and known limits

| Language | Frameworks / conventions | Endpoints from | Traced through |
|---|---|---|---|
| Java / Kotlin | Spring MVC & WebFlux (`@RestController`, `@RequestMapping`, `@GetMapping`…), JAX-RS (`@Path`, `@GET`…) | class + method annotations, `@RequestMapping` prefixes | services, `*Impl`/`Default*` implementations of interfaces, Spring Data repositories (`JpaRepository<Entity, Id>`), Feign/`@HttpExchange` clients (verb + path), `@ControllerAdvice`/`@ResponseStatus` exception → status, `orElseThrow`, `switchIfEmpty(Mono.error(...))`, `ResponseEntity`/JAX-RS `Response` outcomes, `@PreAuthorize`/`@Secured`/`@RolesAllowed`, `@Valid`, `@Cacheable`, `@Transactional`, `@Async` |
| JavaScript / TypeScript | Express, Koa, Fastify, Hono, NestJS, Next.js (`pages/api`, `app/**/route.ts`) | `router.get(...)`, `app.use('/prefix', router)` mount graphs, `fastify.register(..., {prefix})`, `.route()` chains, NestJS decorators (`@Controller`, `@Get`, `@UseGuards`, `@Roles`, `@HttpCode`, `setGlobalPrefix`) | controllers/services via `require`/`import`, class instances, wrapper functions (`asyncHandler`), inline handlers; middleware classified as auth/validation/rate-limit/cache and inherited from mounts; `res.status(n).json()`, `res.sendStatus`, `reply.code`, `ctx.status`, `NextResponse.json(..., {status})`, `throw new HttpException(msg, 404)`, `createError(404)` |
| Python | Flask (routes, Blueprints, MethodView, flask-restful), FastAPI (`APIRouter` prefixes, `Depends`, `status_code`, `response_model`), Django REST (`@api_view`, ViewSets + routers, `@action`, `permission_classes`), Django `urls.py` | decorators and registrations (real `ast`) | module and relative imports, class methods, `with` blocks, `raise HTTPException(status_code=…)`, `abort(404)`, `jsonify(x), 201`, `JsonResponse(..., status=)`, `HttpResponseNotFound`, `get_object_or_404`, SQLAlchemy sessions, Django ORM, httpx/requests/aiohttp, boto3 |
| Go | net/http (incl. Go 1.22 `"GET /path"` patterns), gin, echo, chi (`Route`/`Group`/`Mount`/`With`), gorilla/mux (`HandleFunc(...).Methods(...)`, `PathPrefix().Subrouter()`), fiber | route registrations inside any function | receiver methods through struct fields (`h.svc.PlaceOrder`), package functions, `http.Error(w, msg, code)`, `w.WriteHeader`, `c.JSON(code, …)`, `echo.NewHTTPError`, `if err != nil { return err }` compressed to one line, `errors.Is`, database/sql, gorm-ish verbs, SNS/SQS/Kafka clients |
| C# | ASP.NET Core attribute routing (`[Route]`, `[HttpGet]`, `[controller]`), minimal APIs (`MapGet`, `MapGroup`, `RequireAuthorization`) | attributes / Map* calls | `Ok()`, `NotFound()`, `CreatedAtAction()`, `StatusCode(500)`, `Results.*`, `[Authorize]`, `[FromBody]`… |
| Specs | OpenAPI 3 / Swagger 2 (JSON; YAML with PyYAML) | `paths` | reconciliation with code: `documented` flag, spec summaries as titles, declared responses/auth; spec-only endpoints listed with a warning |
| Serverless | `serverless.yml` (`http`/`httpApi`/`alb` events), AWS SAM (`AWS::Serverless::Function` `Api`/`HttpApi` events) | function events | handler `file.function` lookup in JS/TS/Python/Java |

## What is not seen

- Routes built from data (tables of paths, loops over route lists), reflection-based routing,
  code generation (gRPC gateways, OpenAPI generators without checked-in handlers).
- Interceptors/filters/global guards registered outside the handler chain (e.g. a Spring
  `OncePerRequestFilter`, a NestJS global guard, Express `app.use(auth)` in another entry file)
  are only picked up when they sit on the mount path that leads to the route.
- Dynamic dispatch (`handlers[name](...)`, strategy maps, reflection) → `external`.
- Language features: Kotlin coroutines flows are traced as plain calls; Scala/Play, Ruby/Rails,
  PHP/Laravel, Rust/Actix are not supported.
- Conditions are humanised by heuristics; unusual expressions fall back to lightly cleaned code.
- Calls are followed up to `max_depth` levels (default 4) and `max_steps_per_endpoint` (400).

## Extending recognition without code changes

`.apiflow.json`:

```json
{
  "io_patterns": {"io.http": ["\\bRiskEngineClient\\b"], "io.queue": ["\\bOutboxWriter\\b"]},
  "noise_patterns": ["\\bMetricsHelper\\.", "\\.trace\\("],
  "auth_patterns": ["\\bEntitlementChecker\\b"],
  "validation_patterns": ["\\bSchemaGuard\\b"],
  "feature_flag_patterns": ["\\bFlagService\\.on\\("],
  "endpoint_titles": {"POST /api/v1/orders": "Place an order"}
}
```
