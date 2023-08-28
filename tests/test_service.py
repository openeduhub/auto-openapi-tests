import functools
from collections.abc import Iterable
from typing import Any

import hypothesis.strategies as st
import requests
from hypothesis import given, settings
from openapi_spec_validator import validate_spec_url


def get(*args: str) -> requests.Response:
    return requests.get("/".join(args))


def get_json(*args: str):
    return get(*args).json()


def test_get_openapi_spec(api: str, spec_loc: str):
    r = get(api, spec_loc)
    assert r.status_code == 200


def test_openapi_spec_is_valid(api: str, spec_loc: str):
    validate_spec_url(f"{api}/{spec_loc}")


@st.composite
def json_object(draw, schema: dict[str, Any], version: str) -> dict[str, Any]:
    result = dict()
    for prop, prop_spec in schema["properties"].items():
        if "enum" in prop_spec:
            values = prop_spec["enum"]
            value = draw(st.sampled_from(values))

        else:
            match prop_spec["type"]:
                case "string":
                    min_length = prop_spec.get("minLength", 0)
                    max_length = prop_spec.get("maxLength", None)
                    value = draw(st.text(min_size=min_length, max_size=max_length))
                case "number":
                    min_value = prop_spec.get("minimum", None)
                    max_value = prop_spec.get("maximum", None)
                    exclude_min = prop_spec.get("exclusiveMinimum", False)
                    exclude_max = prop_spec.get("exclusiveMaximum", False)
                    # starting with openapi version 3.1.0,
                    # exclusive... is no longer a bool
                    if type(exclude_min) != bool:
                        min_value = min_value or exclude_min
                        exclude_min = "exclusiveMinimum" in prop_spec

                    if type(exclude_max) != bool:
                        max_value = max_value or exclude_max
                        exclude_max = "exclusiveMaximum" in prop_spec

                    value = draw(
                        st.floats(
                            min_value=min_value,
                            max_value=max_value,
                            exclude_min=exclude_min,
                            exclude_max=exclude_max,
                            allow_infinity=False,
                        )
                    )

                case "boolean":
                    value = draw(st.booleans())

                case not_matched:
                    raise NotImplementedError(
                        f"Generating data for the JSON type {not_matched} not implemented"
                    )

        result[prop] = value

    return result


def nested_get(dic: dict[str, Any], keys: Iterable[str]) -> Any:
    """Access a nested dictionary, skipping keys that are not found."""
    for key in keys:
        if key not in dic:
            continue

        dic = dic[key]

    return dic


@given(data=st.data())
@settings(deadline=None)
def test_end_points_success(data, api: str, spec_loc: str, skip_endpoints: list[str]):
    spec = get_json(api, spec_loc)

    if not "paths" in spec:
        return

    for end_point, end_point_requests in spec["paths"].items():
        if end_point in skip_endpoints:
            continue

        for request_type, request_spec in end_point_requests.items():
            if request_type == "get":
                request_fun = functools.partial(requests.get, url=api + end_point)

            if request_type == "post":
                request_fun = functools.partial(requests.post, url=api + end_point)

            # if the request type is not get or post, skip it
            else:
                continue

            if "requestBody" not in request_spec:
                generated_data = None

            else:
                data_schema_ref = request_spec["requestBody"]["content"][
                    "application/json"
                ]["schema"]["$ref"]

                data_schema = nested_get(spec, data_schema_ref.split("/"))
                generated_data = data.draw(
                    json_object(schema=data_schema, version=spec["openapi"])
                )

            r = request_fun(json=generated_data)
            assert r.status_code == 200
