import streamlit as st


TYPE_LABELS = {
    "home": "Residential",
    "business": "Commercial",
    "public": "Public",
}
TYPE_ICONS = {
    "home": "⌂",
    "business": "▦",
    "public": "▤",
}


class DashboardHeader:
    """Render a dashboard page heading and its subtitle."""

    def __init__(self, title, subtitle):
        self.title = title
        self.subtitle = subtitle

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("title must be a non-empty string")
        self._title = value.strip()

    @property
    def subtitle(self):
        return self._subtitle

    @subtitle.setter
    def subtitle(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("subtitle must be a non-empty string")
        self._subtitle = value.strip()

    def initialize(self):
        """Render the page heading."""
        st.title(self.title, anchor=False)
        st.caption(self.subtitle)


class MetricCard:
    """Display one dashboard metric in a styled Streamlit container."""

    def __init__(self, label, value, key, icon=None, delta=None):
        self.label = label
        self.value = value
        self.key = key
        self.icon = icon
        self.delta = delta

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("label must be a non-empty string")
        self._label = value.strip()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value is None:
            raise ValueError("value cannot be None")
        self._value = value

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("key must be a non-empty string")
        self._key = value.strip()

    @property
    def icon(self):
        return self._icon

    @icon.setter
    def icon(self, value):
        if value is not None and not isinstance(value, str):
            raise ValueError("icon must be a string or None")
        self._icon = value

    @property
    def delta(self):
        return self._delta

    @delta.setter
    def delta(self, value):
        if value is not None and not isinstance(value, str):
            raise ValueError("delta must be a string or None")
        self._delta = value

    def initialize(self):
        """Render the metric inside a keyed container."""
        with st.container(border=True, key=self.key):
            st.metric(
                self.label,
                self.value,
                delta=self.delta,
                delta_color="normal",
                icon=self.icon,
            )


class PropertyCard:
    """Render a building summary and let users select it for details."""

    def __init__(self, building):
        self.building = building

    @property
    def building(self):
        return self._building

    @building.setter
    def building(self, value):
        required = {"id", "name", "type", "floor_area_m2"}
        if not isinstance(value, dict) or not required.issubset(value):
            raise ValueError(f"building must include {', '.join(sorted(required))}")
        if not isinstance(value["name"], str) or not value["name"].strip():
            raise ValueError("building name must be a non-empty string")
        if value["floor_area_m2"] <= 0:
            raise ValueError("floor_area_m2 must be greater than zero")
        self._building = value

    def initialize(self):
        """Render the card; return True when its details button is clicked."""
        building = self.building
        kind = building["type"]
        category = TYPE_LABELS.get(kind, kind.title())
        icon = TYPE_ICONS.get(kind, "▦")
        visual_kind = kind if kind in TYPE_LABELS else "public"

        with st.container(border=True, key=f"property_card_{building['id']}"):
            st.markdown(
                f"<div class='property-visual property-visual-{visual_kind}'>"
                f"<span>{icon}</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"##### {category}")
            st.markdown(f"### {building['name']}")
            st.caption(f"{building['floor_area_m2']:,.0f} m²")
            return st.button(
                "View details →",
                key=f"view_building_{building['id']}",
                width="stretch",
            )
