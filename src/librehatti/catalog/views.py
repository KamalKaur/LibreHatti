from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Sum

from librehatti.catalog.models import Category
from librehatti.catalog.models import Product
from librehatti.catalog.models import *
from librehatti.catalog.forms import AddCategory,TransportForm1,TransportForm2
from librehatti.catalog.models import Transport
from librehatti.catalog.forms import ItemSelectForm

from librehatti.prints.helper import num2eng

from librehatti.suspense.models import SuspenseOrder

import simplejson

def index(request):
    """
    It lists all the products and the user can select any product
    and can add them to the cart.
    """
    """error = {}
    categorylist = Category.objects.all()

    if categorylist.count() == 0:
        nocategory = True
        return render(request, 'catalog.html', {'nocategory': nocategory})
    productlist = Product.objects.all();

    if productlist.count() == 0:
        noproduct = True
        return render(request, 'catalog.html', {'noproduct': noproduct})

    return render(request,'catalog.html', {'productlist': productlist,
               'categorylist': categorylist})

    pass"""
    return render(request,'index.html',{})


def add_categories(request):
    """
    It allows the user to add categories.
    """

    if request.method == 'POST' :
        form = AddCategory(request.POST)
        if form.is_valid():
            return HttpResponseRedirec('/')
    else:
        form = AddCategory()
    return render(request, 'addCategory.html', {
            'form':form
    })


def transport(request):
    form = TransportForm1()
    temp = {'TransportForm':form}
    return render (request, 'bills/form.html',temp)


def transport_bill(request):
    if request.method == 'POST':
        form = TransportForm1(request.POST)
        if form.is_valid():
           
            if 'button1' in request.POST:
                    vehicle_id = request.POST['vehicle_id']
                    job_id = request.POST['job_id']
                    kilometer = float(request.POST['kilometer'])          
                    date = request.POST['date']
                    rate = float(request.POST['rate'])
                    total = rate*kilometer
                    obj = Transport(vehicle_id=vehicle_id, job_id=job_id, 
                           kilometer=kilometer, Date=date, rate=rate, 
                           total=total) 
                    obj.save()
                    temp = Transport.objects.filter(job_id=obj.job_id)
                    total_amount = Transport.objects.filter(job_id=obj.job_id
                           ).aggregate(Sum('total')).get('total__sum', 0.00)
                    return render(request,'bills/transport_bill.html', 
                           {'temp' : temp, 'words' : num2eng(total_amount), 
                            'total_amount' : total_amount}) 

            else:
                    vehicle_id = request.POST['vehicle_id']
                    job_id = request.POST['job_id']
                    kilometer = float(request.POST['kilometer'])
                    date = request.POST['date']
                    rate = float(request.POST['rate'])
                    total = rate * kilometer
                    obj = Transport(vehicle_id=vehicle_id, job_id=job_id, 
                                    kilometer=kilometer, Date=date, rate=rate, 
                                    total=total) 
                    obj.save()
                         
    else:
        form = TransportForm1()
    return render(request, 'bills/form.html', {'TransportForm':form}) 

"""
This view allows filtering of sub category according to parent category of 
item.
"""
def select_sub_category(request):
    parent_category = request.GET['cat_id']
    sub_categories = Category.objects.filter(parent=parent_category)
    sub_category_dict = {}
    for sub_category in sub_categories:
        sub_category_dict[sub_category.id] = sub_category.name
    return HttpResponse(simplejson.dumps(sub_category_dict))

"""
This view allows filtering of item according to sub category of item.
"""
def select_item(request):
    cat_id = request.GET['cat_id']
    products = Product.objects.filter(category = cat_id)
    product_dict = {}
    for product in products:
        product_dict[product.id] = product.name
    return HttpResponse(simplejson.dumps(product_dict))     


"""
This view calculate taxes on purchased order, bill data
and save those values in database.
"""
def bill_cal(request):
    old_post = request.session.get('old_post')
    purchase_order_id = request.session.get('purchase_order_id')

    suffix = "/search_result/?search="
    prefix = "&Order=Order+Search"
    url = suffix + str(purchase_order_id) + prefix

    purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
    purchase_item = PurchasedItem.objects.\
    filter(purchase_order=purchase_order_id).aggregate(Sum('price'))
    price_total = purchase_item['price__sum']
    surcharge = Surcharge.objects.values('id','value','taxes_included')
    delivery_rate = Surcharge.objects.values('value').filter(tax_name = 'Transportation')
    distance = SuspenseOrder.objects.filter(purchase_order = purchase_order_id).\
        aggregate(Sum('distance_estimated'))
    if distance['distance_estimated__sum']:
        delivery_charges = int(distance['distance_estimated__sum'])*\
            delivery_rate[0]['value']

    else:
        delivery_charges = 0

    for value in surcharge:
        surcharge_id = value['id']
        surcharge_value = value['value']
        surcharge_tax = value['taxes_included']
        if surcharge_tax == 1:
            taxes = (price_total * surcharge_value)/100
            surcharge_obj = Surcharge.objects.get(id=surcharge_id)
            taxes_applied = TaxesApplied(purchase_order = purchase_order,
            surcharge = surcharge_obj, tax = taxes)
            taxes_applied.save()
    taxes_applied_obj = TaxesApplied.objects.\
    filter(purchase_order=purchase_order_id).aggregate(Sum('tax'))
    tax_total = taxes_applied_obj['tax__sum']
    grand_total = price_total + tax_total + delivery_charges
    bill = Bill(purchase_order = purchase_order, total_cost = price_total,
    total_tax = tax_total, grand_total = grand_total,
    delivery_charges = delivery_charges)
    bill.save()
    request.session['old_post'] = old_post
    request.session['purchase_order_id'] = purchase_order_id
    return HttpResponseRedirect(url)

def list_products(request):
    all_products = Product.objects.all()
    all_categories=Category.objects.all()
    products_dict = { }
    for one_category in all_categories:
        if one_category.is_leaf_node():
	    products_list = Product.objects.filter(category=one_category)
	    attributes_dict = { }
	    for one_product in products_list:
	    	attributes_list = Catalog.objects.filter(product = one_product)
		attributes_dict[one_product] = attributes_list
            products_dict[one_category.name] = attributes_dict
    return render(request,'list_products.html',{'nodes':all_categories, 'products_dict':products_dict})

