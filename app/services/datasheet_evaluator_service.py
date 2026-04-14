from typing import List, Dict, Any, Optional
from app.schemas.datasheet import EvaluateDatasheetRequest, EvaluateDatasheetResultItem
from app.services.basic_operations_service import BasicOperationsService
from app.models import Rate, Quota
from app.engine.time_models import TimeDuration, TimeUnit

# Campos propios de un endpoint — todo lo que no esté aquí es un alias
_KNOWN_ENDPOINT_KEYS = {"rate", "quota", "workload", "cost_per_request"}

# Alias de nombres de unidad v0.3 → nombre del enum TimeUnit
_UNIT_ALIASES = {"MIN": "MINUTE"}


class DatasheetEvaluatorService:
    def __init__(self):
        self.basic_ops_service = BasicOperationsService()

    def _normalize_period(self, period_def) -> TimeDuration:
        """Soporta period como string v0.2 ('1min') y como objeto v0.3 ({value, unit})."""
        if isinstance(period_def, dict):
            value = period_def["value"]
            unit_str = str(period_def["unit"]).upper()
            unit_str = _UNIT_ALIASES.get(unit_str, unit_str)
            return TimeDuration(value, TimeUnit[unit_str])
        # v0.2: string "1 min", "1 month", etc. — lo pasa el validator de Rate/Quota
        return str(period_def).replace(" ", "")

    def _parse_rate(self, rate_key: str, max_power_defs: dict) -> Rate:
        if rate_key not in max_power_defs:
            raise KeyError(f"Rate definition '{rate_key}' not found in max_power definitions.")
        r_def = max_power_defs[rate_key]
        return Rate(
            value=int(r_def["value"]),
            unit=str(r_def["unit"]),
            period=self._normalize_period(r_def["period"])
        )

    def _parse_quota(self, quota_key: str, capacity_defs: dict) -> Quota:
        if quota_key not in capacity_defs:
            raise KeyError(f"Quota definition '{quota_key}' not found in capacity definitions.")
        q_def = capacity_defs[quota_key]
        return Quota(
            value=int(q_def["value"]),
            unit=str(q_def["unit"]),
            period=self._normalize_period(q_def["period"])
        )

    def _has_aliases(self, ep_config: dict) -> bool:
        """Detecta si un endpoint tiene aliases (sub-dicts que no son campos conocidos)."""
        if ep_config is None:
            return False
        return any(
            isinstance(v, dict) and k not in _KNOWN_ENDPOINT_KEYS
            for k, v in ep_config.items()
        )

    def evaluate(self, yaml_data: dict, request: EvaluateDatasheetRequest) -> Dict[str, List[EvaluateDatasheetResultItem]]:
        capacity_defs = yaml_data.get("capacity", {}) or {}
        max_power_defs = yaml_data.get("max_power", {}) or {}
        plans = yaml_data.get("plans", {})

        # Si no se pasa plan_name, evalúa todos los planes
        if request.plan_name:
            if request.plan_name not in plans:
                raise KeyError(f"Plan '{request.plan_name}' not found. Valid plans are: {list(plans.keys())}")
            plans_to_process = {request.plan_name: plans[request.plan_name]}
        else:
            plans_to_process = plans

        results: Dict[str, List[EvaluateDatasheetResultItem]] = {}

        for plan_name, plan_data in plans_to_process.items():
            results[plan_name] = self._evaluate_plan(
                plan_name=plan_name,
                plan_data=plan_data,
                capacity_defs=capacity_defs,
                max_power_defs=max_power_defs,
                request=request,
            )

        return results

    def _evaluate_plan(self, plan_name: str, plan_data: dict, capacity_defs: dict,
                       max_power_defs: dict, request: EvaluateDatasheetRequest) -> List[EvaluateDatasheetResultItem]:
        endpoints_data = plan_data.get("endpoints", {}) or {}

        # Límites heredados del plan
        plan_rates: List[Rate] = []
        plan_quotas: List[Quota] = []
        if plan_rate_key := plan_data.get("rate"):
            plan_rates.append(self._parse_rate(plan_rate_key, max_power_defs))
        if plan_quota_key := plan_data.get("quota"):
            plan_quotas.append(self._parse_quota(plan_quota_key, capacity_defs))

        # Filtrar por endpoint_path si se pasa
        if request.endpoint_path:
            if request.endpoint_path not in endpoints_data:
                valid_eps = list(endpoints_data.keys())
                raise KeyError(f"Endpoint '{request.endpoint_path}' not found in plan '{plan_name}'. Valid endpoints are: {valid_eps}")
            target_endpoints = {request.endpoint_path: endpoints_data[request.endpoint_path]}
        else:
            target_endpoints = endpoints_data

        results = []

        for ep_path, ep_config in target_endpoints.items():
            ep_config = ep_config or {}

            # Límites a nivel de endpoint (pueden convivir con aliases en v0.3)
            ep_rates = list(plan_rates)
            ep_quotas = list(plan_quotas)
            if ep_rate_key := ep_config.get("rate"):
                ep_rates.append(self._parse_rate(ep_rate_key, max_power_defs))
            if ep_quota_key := ep_config.get("quota"):
                ep_quotas.append(self._parse_quota(ep_quota_key, capacity_defs))

            if self._has_aliases(ep_config):
                # Endpoint con aliases — los campos conocidos son heredados, el resto son aliases
                alias_entries = {
                    k: v for k, v in ep_config.items()
                    if k not in _KNOWN_ENDPOINT_KEYS and isinstance(v, dict)
                }

                if request.alias:
                    if request.alias not in alias_entries:
                        raise KeyError(f"Alias '{request.alias}' not found in endpoint '{ep_path}'. Valid aliases are: {list(alias_entries.keys())}")
                    alias_entries = {request.alias: alias_entries[request.alias]}

                for alias_name, alias_config in alias_entries.items():
                    res = self._process_node(
                        node_config=alias_config,
                        capacity_defs=capacity_defs,
                        max_power_defs=max_power_defs,
                        inherited_rates=ep_rates,
                        inherited_quotas=ep_quotas,
                        operation=request.operation,
                        operation_params=request.operation_params,
                    )
                    results.append(EvaluateDatasheetResultItem(
                        endpoint=ep_path, alias=alias_name, result=res
                    ))
            else:
                if request.alias:
                    raise ValueError(f"Endpoint '{ep_path}' has no aliases, but an alias was provided.")

                res = self._process_node(
                    node_config=ep_config,
                    capacity_defs=capacity_defs,
                    max_power_defs=max_power_defs,
                    inherited_rates=ep_rates,
                    inherited_quotas=ep_quotas,
                    operation=request.operation,
                    operation_params=request.operation_params,
                )
                results.append(EvaluateDatasheetResultItem(
                    endpoint=ep_path, alias="default", result=res
                ))

        return results

    def _process_node(self, node_config: dict, capacity_defs: dict, max_power_defs: dict,
                      inherited_rates: List[Rate], inherited_quotas: List[Quota],
                      operation: str, operation_params: dict) -> Any:

        rates: List[Rate] = list(inherited_rates)
        if rate_key := node_config.get("rate"):
            rates.append(self._parse_rate(rate_key, max_power_defs))

        quotas: List[Quota] = list(inherited_quotas)
        if quota_key := node_config.get("quota"):
            quotas.append(self._parse_quota(quota_key, capacity_defs))

        if not rates and not quotas:
            raise ValueError(f"Neither rate nor quota could be resolved for node config: {node_config}")

        # Busca primero calculate_{op}, luego get_{op} (para rates/quotas/limits)
        method_name = f"calculate_{operation}"
        if not hasattr(self.basic_ops_service, method_name):
            method_name = f"get_{operation}"
        if not hasattr(self.basic_ops_service, method_name):
            raise ValueError(f"Operation '{operation}' is not supported. Engine has no calculate_{operation} or get_{operation} method.")

        method = getattr(self.basic_ops_service, method_name)

        kwargs = dict(operation_params)
        kwargs["rate"] = rates if rates else None
        kwargs["quota"] = quotas if quotas else None

        try:
            return method(**kwargs)
        except TypeError as e:
            raise ValueError(f"Invalid parameters for operation '{operation}': {str(e)}")
