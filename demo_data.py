import pandas as pd

def _trend(values, target):
    d=pd.date_range('2026-08-01', periods=len(values), freq='D')
    return pd.DataFrame({'Date':d,'Actual':values,'Target':[target]*len(values)})

def get_shipments():
    r=[
    ['MH/26-27/0519','Scootsy','Bavla','MN-FARALI-37',440,440,1456,36,0,36,False,35],
    ['MH/26-27/0533','BigBasket','Delhi NCR','MN-SAB-100',150,150,706,17,11,6,True,18],
    ['MH/26-27/0535','BigBasket','Hyderabad','MN-SAB-100',220,220,1456,9,1,8,False,40],
    ['MH/26-27/0537','BigBasket','Bangalore','MN-SAB-100',220,220,1456,9,1,8,False,40],
    ['MH/26-27/0538','RK WorldInfocom','Lonavala','MN-MIX',2405,2405,4267,14,1,13,True,320],
    ['MH/26-27/0539','RK WorldInfocom','Jhajjar','MN-MIX',2270,2270,4888,35,9,26,False,360],
    ['MH/26-27/0556','RK WorldInfocom','Greater Thane','MN-SKU-X',80,75,1456,38,9,29,False,25],
    ['MH/26-27/0557','RK WorldInfocom','Greater Thane','MN-SKU-Y',40,37.5,1456,36,4,32,False,20],
    ['MH/26-27/0558','BigBasket','Bangalore','MN-MIX',80,80,1456,12,2,10,False,15],
    ['MH/26-27/0570','Scootsy','Lonavala','MN-MIX',370,370,1724,13,3,10,True,30]]
    return pd.DataFrame(r,columns=['Invoice','Customer','City','SKU','Ordered','Shipped','Cost','Order_to_Delivery','Order_to_Ship','Ship_to_Delivery','OTIF','Weight']).assign(Fulfillment=lambda x:x.Shipped/x.Ordered)

def _metric(name,value,target,unit,window,coverage,formula,trend,df,good_when='gte'):
    bad = value < target if good_when=='gte' else value > target
    delta = value-target
    if unit=='%': delta_txt=f"{delta:+.1f} pp"
    elif unit=='₹': delta_txt=f"₹{delta:+.0f}"
    else: delta_txt=f"{delta:+.1f} d"
    return {'name':name,'value':f'{value:.1f}{unit}' if unit!='₹' else f'₹{value:,.0f}','delta':delta_txt,'target':f'≥{target}{unit}' if good_when=='gte' else f'≤{target}{unit}','window':window,'coverage':coverage,'formula':formula,'trend':trend,'data':df,'bad':bad}

def get_demo_metrics():
    ship=get_shipments()
    calc=ship[['Invoice','Customer','City','SKU','Ordered','Shipped','Fulfillment']].copy(); calc['Fulfillment']=calc['Fulfillment']*100
    fulfillment=_metric('Fulfillment',92.5,95,'%','01 Aug → 26 Aug','1,823 / 1,842 order lines','Shipped quantity ÷ ordered quantity × 100',_trend([95,96,94,93,95,94,92,93,94,91,92,93,92,92.5],95),calc)
    otif=_metric('OTIF',87,95,'%','01 Aug → 26 Aug','1,842 / 1,901 shipments','Shipments delivered on/before expected date ÷ eligible shipments × 100',_trend([94,93,92,91,90,92,89,88,90,87,88,87,86,87],95),ship[['Invoice','Customer','City','OTIF']])
    cost=_metric('Cost / Shipment',441,400,'₹','01 Aug → 26 Aug','1,823 / 1,842 shipments','Total billing charges ÷ invoice shipments',_trend([382,390,401,398,405,411,420,417,425,431,436,438,440,441],400),ship[['Invoice','Customer','City','SKU','Cost','Weight']],'lte')
    o2s=ship['Order_to_Ship'].mean(); s2d=ship['Ship_to_Delivery'].mean(); o2d=ship['Order_to_Delivery'].mean()
    order_to_ship=_metric('Order → Ship',o2s,5,' d','01 Aug → 26 Aug','98.1% valid shipment dates','Dispatch date − order date',_trend([4.1,4.3,4.5,4.7,4.9,5.0,5.2,5.1,5.3,5.2,5.1,5.0,5.1,o2s],5),ship[['Invoice','Customer','City','SKU','Order_to_Ship']],'lte')
    ship_to_delivery=_metric('Ship → Delivery',s2d,2,' d','01 Aug → 26 Aug','97.4% valid delivery dates','Delivery date − dispatch date',_trend([1.8,1.9,2.0,2.1,2.0,2.2,2.1,2.3,2.4,2.5,2.7,2.8,3.0,s2d],2),ship[['Invoice','Customer','City','SKU','Ship_to_Delivery']],'lte')
    delivery=_metric('Order → Delivery',o2d,5,' d','01 Aug → 26 Aug','96.9% valid end-to-end dates','Delivery date − order date',_trend([6.0,6.2,6.4,6.5,6.8,6.9,7.1,7.2,7.4,7.6,7.8,8.0,8.1,o2d],5),ship[['Invoice','Customer','City','SKU','Order_to_Delivery']],'lte')
    lead=[
      {'name':'Pending to Ship','value':'146','delta':'+32','target':'<100','bad':True,'progress':0.72,'lag':'Fulfillment / Order → Ship'},
      {'name':'Dispatch SLA','value':'92%','delta':'-3 pp','target':'≥95%','bad':True,'progress':0.92,'lag':'Order → Ship'},
      {'name':'Supplier OTIF','value':'89%','delta':'-6 pp','target':'≥95%','bad':True,'progress':0.89,'lag':'Fulfillment / Inventory'}]
    return {'fulfillment':fulfillment,'otif':otif,'cost':cost,'order_to_ship':order_to_ship,'ship_to_delivery':ship_to_delivery,'delivery':delivery,'lead_measures':lead}

def get_quality():
    return pd.DataFrame([
      ['Unmapped SKU',7,'🔴 Action required','Exclude from official metrics','Map / Exclude / Historic'],
      ['Duplicate rows',12,'🟡 Review','Deduplicate; retain raw rows','Deduplicate / Keep'],
      ['Missing delivery date',4,'🟡 Warning','Exclude from delivery metrics','Exclude / Historic'],
      ['Missing EDD',31,'🟡 Warning','Exclude from supplier OTIF','Exclude'],
      ['Unknown city',3,'🔴 Action required','City drilldown incomplete','Map / Exclude']],
      columns=['Issue','Count','Status','Current treatment','User decision'])
