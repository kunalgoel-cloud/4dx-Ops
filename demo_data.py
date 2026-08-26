import pandas as pd


def _trend(values, target):
    d = pd.date_range('2026-08-01', periods=len(values), freq='D')
    return pd.DataFrame({'Date': d, 'Actual': values, 'Target': [target] * len(values)})


def get_shipments():
    rows = [
        ['MH/26-27/0519','Scootsy','Bavla','MN-FARALI-37',440,440,1456,36,0,36,False,35,'2026-07-28','2026-08-02','2026-09-07',30000],
        ['MH/26-27/0533','BigBasket','Delhi NCR','MN-SAB-100',150,150,706,17,11,6,True,18,'2026-08-03','2026-08-14','2026-08-20',12000],
        ['MH/26-27/0535','BigBasket','Hyderabad','MN-SAB-100',220,220,1456,9,1,8,False,40,'2026-08-04','2026-08-05','2026-08-13',18500],
        ['MH/26-27/0537','BigBasket','Bangalore','MN-SAB-100',220,220,1456,9,1,8,False,40,'2026-08-05','2026-08-06','2026-08-14',19000],
        ['MH/26-27/0538','RK WorldInfocom','Lonavala','MN-MIX',2405,2405,4267,14,1,13,True,320,'2026-08-05','2026-08-06','2026-08-19',48000],
        ['MH/26-27/0539','RK WorldInfocom','Jhajjar','MN-MIX',2270,2270,4888,35,9,26,False,360,'2026-08-06','2026-08-15','2026-09-10',45500],
        ['MH/26-27/0556','RK WorldInfocom','Greater Thane','MN-SKU-X',80,75,1456,38,9,29,False,25,'2026-08-07','2026-08-16','2026-09-14',9200],
        ['MH/26-27/0557','RK WorldInfocom','Greater Thane','MN-SKU-Y',40,37.5,1456,36,4,32,False,20,'2026-08-08','2026-08-12','2026-09-13',8100],
        ['MH/26-27/0558','BigBasket','Bangalore','MN-MIX',80,80,1456,12,2,10,False,15,'2026-08-09','2026-08-11','2026-08-21',14000],
        ['MH/26-27/0570','Scootsy','Lonavala','MN-MIX',370,370,1724,13,3,10,True,30,'2026-08-10','2026-08-13','2026-08-23',22000],
    ]
    cols=['Invoice','Customer','City','SKU','Ordered','Shipped','Cost','Order_to_Delivery','Order_to_Ship','Ship_to_Delivery','OTIF','Weight','Invoice_Date','Ship_Date','Delivery_Date','Invoice_Value']
    df=pd.DataFrame(rows,columns=cols)
    for c in ['Invoice_Date','Ship_Date','Delivery_Date']:
        df[c]=pd.to_datetime(df[c])
    df['Fulfillment']=df['Shipped']/df['Ordered']
    df['Cost_pct_Invoice']=df['Cost']/df['Invoice_Value']*100
    return df


def get_sku_supply():
    return pd.DataFrame([
        ['MN-FARALI-37','Supplier A',18,4.0,3.0,7.0,365,30000,1.2],
        ['MN-SAB-100','Supplier B',14,3.5,2.8,6.3,390,16500,1.8],
        ['MN-MIX','Supplier C',21,5.2,3.4,8.6,472,37000,2.4],
        ['MN-SKU-X','Supplier D',24,6.0,3.6,9.6,510,9200,4.1],
        ['MN-SKU-Y','Supplier D',22,5.5,3.8,9.3,520,8100,4.9],
    ],columns=['SKU','Supplier','Material_Lead_Time','Order_to_Ship','Ship_to_Delivery','Order_to_Delivery','Cost_per_Shipment','Invoice_Value','Cost_pct_Invoice'])


def _metric(name,value,target,unit,window,coverage,formula,trend,df,good_when='gte'):
    bad=value < target if good_when=='gte' else value > target
    delta=value-target
    if unit=='%': delta_txt=f'{delta:+.1f} pp'
    elif unit=='₹': delta_txt=f'₹{delta:+.0f}'
    else: delta_txt=f'{delta:+.1f} d'
    return {'name':name,'value':f'{value:.1f}{unit}' if unit!='₹' else f'₹{value:,.0f}','delta':delta_txt,'target':f'≥{target}{unit}' if good_when=='gte' else f'≤{target}{unit}','window':window,'coverage':coverage,'formula':formula,'trend':trend,'data':df,'bad':bad}


def get_demo_metrics():
    ship=get_shipments(); sku=get_sku_supply()
    calc=ship[['Invoice','Invoice_Date','Ship_Date','Delivery_Date','Customer','City','SKU','Ordered','Shipped','Fulfillment']].copy(); calc['Fulfillment']*=100
    fulfillment=_metric('Fulfillment',calc['Shipped'].sum()/calc['Ordered'].sum()*100,95,'%','01 Aug → 26 Aug','10 / 10 shipment records','Total shipped quantity ÷ total ordered quantity × 100',_trend([95,96,94,93,95,94,92,93,94,91,92,93,92,92.5],95),calc)
    otif=_metric('OTIF',ship['OTIF'].mean()*100,95,'%','01 Aug → 26 Aug','10 / 10 eligible shipments','On-time shipments ÷ eligible shipments × 100',_trend([94,93,92,91,90,92,89,88,90,87,88,87,86,87],95),ship[['Invoice','Invoice_Date','Ship_Date','Delivery_Date','Customer','City','OTIF']])
    avg_invoice=ship['Invoice_Value'].mean()
    avg_inv=_metric('Average Invoice Value',avg_invoice,20000,'₹','01 Aug → 26 Aug','10 / 10 invoices','Total invoice value ÷ invoice count',_trend([18000,18500,19000,19500,20000,20500,21000,20800,20500,20200,20100,20000,19800,avg_invoice],20000),ship[['Invoice','Invoice_Date','Customer','City','SKU','Invoice_Value']],'gte')
    cost=ship['Cost'].sum()/len(ship)
    cost_metric=_metric('Cost / Shipment',cost,400,'₹','01 Aug → 26 Aug','10 / 10 shipments','Total billing charges ÷ shipment count',_trend([382,390,401,398,405,411,420,417,425,431,436,438,440,cost],400),ship[['Invoice','Invoice_Date','Customer','City','SKU','Cost','Invoice_Value']],'lte')
    cost_pct=ship['Cost'].sum()/ship['Invoice_Value'].sum()*100
    cost_pct_metric=_metric('Cost / Invoice Value',cost_pct,3.0,'%','01 Aug → 26 Aug','10 / 10 shipments','Total shipment cost ÷ total invoice value × 100',_trend([2.1,2.2,2.4,2.5,2.6,2.7,2.8,2.9,3.0,3.1,3.2,3.1,3.2,cost_pct],3.0),ship[['Invoice','Invoice_Date','Customer','City','SKU','Cost','Invoice_Value','Cost_pct_Invoice']],'lte')
    o2s=ship['Order_to_Ship'].mean(); s2d=ship['Ship_to_Delivery'].mean(); o2d=ship['Order_to_Delivery'].mean(); mat=sku['Material_Lead_Time'].mean()
    order_to_ship=_metric('Order → Ship',o2s,5,' d','01 Aug → 26 Aug','10 / 10 valid order/ship dates','Ship date − order date',_trend([4.1,4.3,4.5,4.7,4.9,5.0,5.2,5.1,5.3,5.2,5.1,5.0,5.1,o2s],5),ship[['Invoice','Invoice_Date','Ship_Date','Delivery_Date','Customer','City','SKU','Order_to_Ship']],'lte')
    ship_to_delivery=_metric('Ship → Delivery',s2d,2,' d','01 Aug → 26 Aug','10 / 10 valid ship/delivery dates','Delivery date − ship date',_trend([1.8,1.9,2.0,2.1,2.0,2.2,2.1,2.3,2.4,2.5,2.7,2.8,3.0,s2d],2),ship[['Invoice','Invoice_Date','Ship_Date','Delivery_Date','Customer','City','SKU','Ship_to_Delivery']],'lte')
    delivery=_metric('Order → Delivery',o2d,5,' d','01 Aug → 26 Aug','10 / 10 valid order/delivery dates','Delivery date − order date',_trend([6.0,6.2,6.4,6.5,6.8,6.9,7.1,7.2,7.4,7.6,7.8,8.0,8.1,o2d],5),ship[['Invoice','Invoice_Date','Ship_Date','Delivery_Date','Customer','City','SKU','Order_to_Delivery']],'lte')
    material=_metric('Material Lead Time',mat,15,' d','01 Aug → 26 Aug','5 / 5 SKUs with PO order + receipt dates','Actual supply/receipt date − PO order date',_trend([14,15,16,17,18,18,19,20,19,20,21,21,22,mat],15),sku[['SKU','Supplier','Material_Lead_Time']],'lte')
    lead=[
      {'name':'Material Lead Time','value':f'{mat:.1f} d','delta':f'{mat-15:+.1f} d','target':'≤15 d','bad':mat>15,'progress':min(mat/15,1),'lag':'Inventory / Fulfillment'},
      {'name':'Pending to Ship','value':'146','delta':'+32','target':'<100','bad':True,'progress':.72,'lag':'Fulfillment / Order → Ship'},
      {'name':'Dispatch SLA','value':'92%','delta':'-3 pp','target':'≥95%','bad':True,'progress':.92,'lag':'Order → Ship'},
      {'name':'Supplier OTIF','value':'89%','delta':'-6 pp','target':'≥95%','bad':True,'progress':.89,'lag':'Material availability / Fulfillment'}]
    return {'fulfillment':fulfillment,'otif':otif,'avg_invoice':avg_inv,'cost':cost_metric,'cost_pct':cost_pct_metric,'order_to_ship':order_to_ship,'ship_to_delivery':ship_to_delivery,'delivery':delivery,'material_lead_time':material,'lead_measures':lead,'sku_supply':sku}


def get_quality():
    return pd.DataFrame([
      ['Unmapped SKU',7,'🔴 Action required','Exclude from official metrics','Map / Exclude / Historic'],
      ['Duplicate rows',12,'🟡 Review','Deduplicate; retain raw rows','Deduplicate / Keep'],
      ['Missing delivery date',4,'🟡 Warning','Exclude from delivery metrics','Exclude / Historic'],
      ['Missing EDD',31,'🟡 Warning','Exclude from supplier OTIF','Exclude'],
      ['Unknown city',3,'🔴 Action required','City drilldown incomplete','Map / Exclude']],
      columns=['Issue','Count','Status','Current treatment','User decision'])


def get_unmapped_demo_items():
    return pd.DataFrame([
      ['SKU','8908024143123_75'],['Customer','New Customer Pvt Ltd'],['City','Gurugram NCR']],columns=['Type','Source Value'])
