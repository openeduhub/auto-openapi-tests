import functools
from collections.abc import Iterable
from typing import Any

import hypothesis.strategies as st
import requests
from hypothesis import given, settings
from openapi_spec_validator import validate_spec_url


def test_get_openapi_spec(api: str, spec_loc: str):
    r = requests.get(api + spec_loc)
    assert r.status_code == 200


def test_openapi_spec_is_valid(api: str, spec_loc: str):
    validate_spec_url(api + spec_loc)


@st.composite
def draw_from_type(draw, prop_spec: dict[str, Any]) -> Any:
    if "enum" in prop_spec:
        # enums specify their possible values directly
        values = prop_spec["enum"]
        return draw(st.sampled_from(values))

    @st.composite
    def handle_composite(draw, key: str):
        specs: list[dict[str, Any]] = prop_spec[key]
        return draw(st.one_of(*[draw_from_type(spec) for spec in specs]))

    for key in ["anyOf", "oneOf", "allOf"]:
        # handle all elements of such unions identically
        try:
            return draw(handle_composite(key))
        except KeyError:
            continue

    if "type" not in prop_spec:
        raise ValueError(
            f"No type information was found in the property sub-specification {prop_spec}. This could be due to the use of an untyped array, or because the specified type is not implemented in this test-suite"
        )

    match prop_spec["type"]:
        case "string":
            min_length = prop_spec.get("minLength", 0)
            max_length = prop_spec.get("maxLength", None)
            return draw(st.text(min_size=min_length, max_size=max_length))

        case "number":
            min_value = prop_spec.get("minimum", None)
            max_value = prop_spec.get("maximum", None)
            exclude_min = prop_spec.get("exclusiveMinimum", False)
            exclude_max = prop_spec.get("exclusiveMaximum", False)
            # starting with openapi version 3.1.0,
            # exclusive_... is no longer a bool
            if type(exclude_min) != bool:
                min_value = min_value or exclude_min
                exclude_min = "exclusiveMinimum" in prop_spec

            if type(exclude_max) != bool:
                max_value = max_value or exclude_max
                exclude_max = "exclusiveMaximum" in prop_spec

            return draw(
                st.floats(
                    min_value=min_value,
                    max_value=max_value,
                    exclude_min=exclude_min,
                    exclude_max=exclude_max,
                    allow_infinity=False,
                )
            )

        case "boolean":
            return draw(st.booleans())

        case "array":
            # draw recursively, respecting the specified constraints
            constraints = {
                "min_size": prop_spec.get("minItems", 0),
                "max_size": prop_spec.get("maxItems", 10),
                "unique": prop_spec.get("uniqueItems", False),
            }
            sub_spec = prop_spec["items"]

            if "oneOf" in sub_spec:
                # an array of oneOf contains a list of only one type
                return draw(
                    st.lists(
                        st.one_of(
                            *[draw_from_type(spec) for spec in sub_spec["oneOf"]]
                        ),
                        **constraints,
                    )
                )

            return draw(st.lists(draw_from_type(sub_spec), **constraints))

        case not_matched:
            raise NotImplementedError(
                f"Generating data for the JSON type {not_matched} not implemented"
            )


@st.composite
def json_object(draw, schema: dict[str, Any], version: str) -> dict[str, Any]:
    return {
        prop: draw(draw_from_type(prop_spec))
        for prop, prop_spec in schema["properties"].items()
    }


def nested_get(dic: dict[str, Any], keys: Iterable[str]) -> Any:
    """Access a nested dictionary, skipping keys that are not found."""
    for key in keys:
        if key not in dic:
            continue

        dic = dic[key]

    return dic


spec = None


@given(data=st.data())
@settings(deadline=None)
def test_end_points_success(data, api: str, spec_loc: str, skip_endpoints: list[str]):
    # only access the openapi spec once
    global spec
    if spec is None:
        spec = requests.get(api + spec_loc).json()

    if not "paths" in spec:
        return

    end_point, end_point_requests = data.draw(
        st.sampled_from(list(spec["paths"].items()))
    )

    if end_point in skip_endpoints:
        return

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
