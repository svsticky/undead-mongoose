from django import forms


class TopUpForm(forms.Form):
    amount = forms.DecimalField(min_value=0, decimal_places=2, required=True)
