def estimate_bill(units, rate=6.5, fixed_charge=80, tax_rate=0.05):
    units=max(0,float(units))
    energy=units*float(rate)
    subtotal=energy+float(fixed_charge)
    tax=subtotal*float(tax_rate)
    return {"units":round(units,2),"rate":float(rate),"energy_charge":round(energy,2),
            "fixed_charge":round(float(fixed_charge),2),"tax":round(tax,2),
            "total":round(subtotal+tax,2),
            "note":"Illustrative estimate only. Replace with the applicable DISCOM tariff and billing rules."}
