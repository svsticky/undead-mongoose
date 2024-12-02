from django import forms

def create_TopUpForm(mollie_client):
    issuers = [(issuer.id, issuer.name) for issuer in mollie_client.methods.get("ideal", include="issuers").issuers]
    class TopUpForm(forms.Form):
        amount = forms.DecimalField(min_value=0, decimal_places=2, required=True)
        issuer = forms.ChoiceField(choices=issuers, label="Bank")
    return TopUpForm