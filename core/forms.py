from django import forms


class StyledFormMixin:
    """Aplica clases y atributos comunes a los widgets del formulario."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.CheckboxSelectMultiple,
                    forms.RadioSelect,
                    forms.HiddenInput,
                ),
            ):
                continue
            clases = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{clases} input".strip()
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 3)
            if isinstance(widget, forms.DateInput):
                widget.input_type = "date"


class StyledForm(StyledFormMixin, forms.Form):
    pass


class StyledModelForm(StyledFormMixin, forms.ModelForm):
    pass
