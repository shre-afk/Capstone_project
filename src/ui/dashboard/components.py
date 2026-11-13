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

    def __init__(self, building, selected=False):
        self.building = building
        self.selected = selected

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
        if kind == "home":
            visual = (
                "<svg class='property-home-illustration' viewBox='0 0 320 180' "
                "role='img' aria-label='Illustration of a home' "
                "xmlns='http://www.w3.org/2000/svg'>"
                "<path d='M0 151c48-14 90-7 134 0s91 5 186-6v35H0z' "
                "fill='#B8D0BE'/>"
                "<circle cx='262' cy='38' r='19' fill='#F3D99B'/>"
                "<path d='M96 151V83l64-49 64 49v68z' fill='#F8F5ED'/>"
                "<path d='m82 87 78-60 78 60-10 13-68-52-68 52z' "
                "fill='#527A67'/>"
                "<path d='M145 105h31v46h-31z' fill='#C78D52'/>"
                "<circle cx='168' cy='129' r='2.5' fill='#F8F5ED'/>"
                "<path d='M111 99h23v25h-23zm78 0h23v25h-23z' "
                "fill='#B9D5E2' stroke='#D6A968' stroke-width='4'/>"
                "<path d='M122 99v25m-11-12h23m55-13v25m-11-12h23' "
                "stroke='#F8F5ED' stroke-width='3'/>"
                "<path d='M74 151c0-16 10-28 22-28s22 12 22 28m105 0"
                "c0-17 11-30 24-30s24 13 24 30' fill='#6F9579'/>"
                "<path d='M159 151v29m-12-14 12 8 12-8' fill='none' "
                "stroke='#D6A968' stroke-width='5' stroke-linecap='round'/>"
                "</svg>"
            )
        elif kind == "business":
            visual = (
                "<svg class='property-type-illustration' viewBox='0 0 320 180' "
                "role='img' aria-label='Commercial office building' "
                "xmlns='http://www.w3.org/2000/svg'>"
                "<path d='M0 151h320v29H0z' fill='#C5D6E0'/>"
                "<path d='M81 151V55l79-35 79 35v96z' fill='#F8F5ED'/>"
                "<path d='M72 57 160 17l88 40-6 12-82-37-82 37z' fill='#52728A'/>"
                "<path d='M104 69h23v21h-23zm45 0h23v21h-23zm45 0h23v21h-23z"
                "M104 105h23v21h-23zm45 0h23v21h-23zm45 0h23v21h-23z' "
                "fill='#B9D5E2' stroke='#D7E1E6' stroke-width='3'/>"
                "<path d='M147 133h26v18h-26z' fill='#D6A968'/>"
                "<path d='M40 151c0-18 12-31 26-31s26 13 26 31m166 0"
                "c0-18 12-31 26-31s26 13 26 31' fill='#78947F'/>"
                "</svg>"
            )
        elif kind == "public":
            visual = (
                "<svg class='property-type-illustration' viewBox='0 0 320 180' "
                "role='img' aria-label='Public civic building' "
                "xmlns='http://www.w3.org/2000/svg'>"
                "<path d='M0 151h320v29H0z' fill='#E6D3B4'/>"
                "<path d='m49 62 111-43 111 43z' fill='#9A744B'/>"
                "<path d='M62 67h196v12H62z' fill='#C39A68'/>"
                "<path d='M75 79h170v64H75z' fill='#F8F5ED'/>"
                "<path d='M62 143h196v10H62z' fill='#9A744B'/>"
                "<path d='M91 82h14v58H91zm37 0h14v58h-14zm44 0h14v58h-14z"
                "m37 0h14v58h-14z' fill='#D6C2A3'/>"
                "<path d='M149 112h22v31h-22z' fill='#C78D52'/>"
                "<circle cx='160' cy='37' r='8' fill='#F3D99B'/>"
                "<path d='M40 153h240v8H40z' fill='#78947F'/>"
                "</svg>"
            )
        else:
            visual = f"<span aria-hidden='true'>{icon}</span>"

        card_key = (
            f"property_card_selected_{building['id']}"
            if self.selected
            else f"property_card_{building['id']}"
        )
        with st.container(border=True, key=card_key):
            st.markdown(
                f"<div class='property-visual property-visual-{visual_kind}'>"
                f"{visual}</div>",
                unsafe_allow_html=True,
            )
            if self.selected:
                st.markdown(
                    "<div class='property-selected'>Selected building</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='property-selected property-selected-placeholder' "
                    "aria-hidden='true'>Selected building</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(f"#### {building['name']}")
            st.caption(f"{category} · {building['floor_area_m2']:,.0f} m²")
            return st.button(
                "View details",
                key=f"view_building_{building['id']}",
                help=f"View details for {building['name']}",
                width="stretch",
            )
