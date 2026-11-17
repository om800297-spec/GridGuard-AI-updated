def recommendations(current_units, previous_units, monthly_bill):
    current=float(current_units or 0); previous=float(previous_units or 0)
    change=((current-previous)/previous*100) if previous>0 else 0
    items=[]
    if change>10:
        items.append({"title":"Review recent consumption increase","detail":f"Usage is {change:.1f}% higher than the comparison period. Check high-use appliances and operating hours.","impact":"High"})
    if current>250:
        items.append({"title":"Shift flexible usage away from peak periods","detail":"Where your tariff supports time-based pricing, schedule flexible loads outside peak periods.","impact":"Medium"})
    items.append({"title":"Track standby consumption","detail":"Switch off devices that do not need to remain on and review standby loads.","impact":"Low"})
    items.append({"title":"Use efficient lighting","detail":"Replace frequently used inefficient lights with suitable LED alternatives.","impact":"Low"})
    if monthly_bill>0:
        items.append({"title":"Set a monthly usage target","detail":f"A 5% reduction against the current estimate would save approximately ₹{monthly_bill*0.05:.0f}, subject to tariff and charges.","impact":"Medium"})
    return items
