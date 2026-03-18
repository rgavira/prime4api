from typing import List, Dict, Any, Optional
from app.schemas.datasheet import EvaluateDatasheetRequest, EvaluateDatasheetResultItem
from app.services.basic_operations_service import BasicOperationsService
from app.models import Rate, Quota


class DatasheetEvaluatorService:
    def __init__(self):
        self.basic_ops_service = BasicOperationsService()

    def _parse_rate(self, rate_key: str, max_power_defs: dict) -> Rate:
        if rate_key not in max_power_defs:
            raise KeyError(f"Rate definition '{rate_key}' not found in max_power definitions.")
        r_def = max_power_defs[rate_key]
        return Rate(
            value=int(r_def["value"]),
            unit=str(r_def["unit"]),
            period=str(r_def["period"]).replace(" ", "")
        )

    def _parse_quota(self, quota_key: str, capacity_defs: dict) -> Quota:
        if quota_key not in capacity_defs:
            raise KeyError(f"Quota definition '{quota_key}' not found in capacity definitions.")
        q_def = capacity_defs[quota_key]
        return Quota(
            value=int(q_def["value"]),
            unit=str(q_def["unit"]),
            period=str(q_def["period"]).replace(" ", "")
        )

    def evaluate(self, yaml_data: dict, request: EvaluateDatasheetRequest) -> List[EvaluateDatasheetResultItem]:
        # 1. Extraer definiciones globales
        capacity_defs = yaml_data.get("capacity", {})
        max_power_defs = yaml_data.get("max_power", {})
        plans = yaml_data.get("plans", {})

        # 2. Navegar al plan
        plan_name = request.plan_name
        if plan_name not in plans:
            raise KeyError(f"Plan '{plan_name}' not found. Valid plans are: {list(plans.keys())}")

        plan_data = plans[plan_name]
        endpoints_data = plan_data.get("endpoints", {})

        # 3. Construir límites heredados del plan (nivel superior)
        plan_rates: List[Rate] = []
        plan_quotas: List[Quota] = []
        if plan_rate_key := plan_data.get("rate"):
            plan_rates.append(self._parse_rate(plan_rate_key, max_power_defs))
        if plan_quota_key := plan_data.get("quota"):
            plan_quotas.append(self._parse_quota(plan_quota_key, capacity_defs))

        results = []

        # 4. Iterar o ir a endpoint específico
        if request.endpoint_path:
            if request.endpoint_path not in endpoints_data:
                valid_eps = list(endpoints_data.keys())
                raise KeyError(f"Endpoint '{request.endpoint_path}' not found in plan '{plan_name}'. Valid endpoints are: {valid_eps}")
            target_endpoints = {request.endpoint_path: endpoints_data[request.endpoint_path]}
        else:
            target_endpoints = endpoints_data

        # 5. Procesar Endpoints y Alias Anidados
        for ep_path, ep_config in target_endpoints.items():

            # Detectar si este endpoint tiene "aliases" (ej: healthy_reputation).
            # Los sub-ítems no tienen 'rate' ni 'quota' directamente en la raiz si tienen alias.
            # Según docu v0.2, si tiene alias, el contenido de ep_config son claves de nombre de alias.
            has_aliases = not ("rate" in ep_config or "quota" in ep_config)

            if has_aliases:
                aliases_to_process = {}
                if request.alias:
                    if request.alias in ep_config:
                        aliases_to_process[request.alias] = ep_config[request.alias]
                    else:
                        valid_aliases = list(ep_config.keys())
                        raise KeyError(f"Alias '{request.alias}' not found in endpoint '{ep_path}'. Valid aliases are: {valid_aliases}")
                else:
                    aliases_to_process = ep_config

                for alias_name, alias_config in aliases_to_process.items():
                    res = self._process_node(
                        node_config=alias_config,
                        capacity_defs=capacity_defs,
                        max_power_defs=max_power_defs,
                        inherited_rates=plan_rates,
                        inherited_quotas=plan_quotas,
                        operation=request.operation,
                        operation_params=request.operation_params
                    )
                    results.append(EvaluateDatasheetResultItem(
                        endpoint=ep_path,
                        alias=alias_name,
                        result=res
                    ))
            else:
                # Es un endpoint plano (sin aliases)
                if request.alias:
                    raise ValueError(f"Endpoint '{ep_path}' has no sub-aliases, but an alias was provided.")

                res = self._process_node(
                    node_config=ep_config,
                    capacity_defs=capacity_defs,
                    max_power_defs=max_power_defs,
                    inherited_rates=plan_rates,
                    inherited_quotas=plan_quotas,
                    operation=request.operation,
                    operation_params=request.operation_params
                )
                results.append(EvaluateDatasheetResultItem(
                    endpoint=ep_path,
                    alias="default",
                    result=res
                ))

        return results

    def _process_node(self, node_config: dict, capacity_defs: dict, max_power_defs: dict,
                      inherited_rates: List[Rate], inherited_quotas: List[Quota],
                      operation: str, operation_params: dict) -> Any:

        # Acumulación jerárquica: partir de los límites heredados y añadir los del nodo
        rates: List[Rate] = list(inherited_rates)
        if rate_key := node_config.get("rate"):
            rates.append(self._parse_rate(rate_key, max_power_defs))

        quotas: List[Quota] = list(inherited_quotas)
        if quota_key := node_config.get("quota"):
            quotas.append(self._parse_quota(quota_key, capacity_defs))

        # Si no hay rate ni quota definidos
        if not rates and not quotas:
            raise ValueError(f"Neither rate nor quota could be resolved for node config: {node_config}")

        # Delegar el cálculo dinámico al BasicOperationsService
        method_name = f"calculate_{operation}"
        if not hasattr(self.basic_ops_service, method_name):
            raise ValueError(f"Operation '{operation}' is not supported. Engine has no {method_name} method.")

        method = getattr(self.basic_ops_service, method_name)

        # Montar y pasar los params kwargs con listas de límites
        kwargs = dict(operation_params)
        kwargs["rate"] = rates if rates else None
        kwargs["quota"] = quotas if quotas else None

        # Ejecutar
        try:
            return method(**kwargs)
        except TypeError as e:
            raise ValueError(f"Invalid parameters for operation '{operation}': {str(e)}")
