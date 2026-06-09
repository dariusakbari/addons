/** @odoo-module **/
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Widget } from "@web/views/widgets/widget";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

	export class XeroDashboardViewNew extends Component {
	static template = "XeroDashboardViewNew";
	setup() {
        this.action = useService("action");
        self = this
rpc("/web/dataset/call_kw/purchase.order/get_pending_order_counts", {   //		PURCHASE
                model: "purchase.order",
                method: "get_pending_order_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                 var pending_order = document.getElementById("pending_order");
                if (!pending_order) {
                    console.warn("pending_order NOT FOUND");
                    return;
                }
                pending_order.innerHTML = res;
                var total_order = res
rpc("/web/dataset/call_kw/purchase.order/get_waiting_bill_counts", {
                model: "purchase.order",
                method: "get_waiting_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                 var completed_bill = document.getElementById("completed_bill");
                if (!completed_bill) {
                    console.warn("completed_bill NOT FOUND");
                    return;
                }
                completed_bill.innerHTML = res;
                var waiting_bill = res
rpc("/web/dataset/call_kw/account.move/get_unpaid_bill_counts", {
                model: "account.move",
                method: "get_unpaid_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var unpaid_order = document.getElementById("unpaid_order");
                if (!unpaid_order) {
                    console.warn("unpaid_order NOT FOUND");
                    return;
                }
                unpaid_order.innerHTML = res;


                var unpaid_order = res
rpc("/web/dataset/call_kw/account.move/get_paid_bill_counts", {
                model: "account.move",
                method: "get_paid_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var paid_order = document.getElementById("paid_order");
                if (!paid_order) {
                    console.warn("paid_order NOT FOUND");
                    return;
                }
                paid_order.innerHTML = res;


                var paid_order = res
rpc("/web/dataset/call_kw/purchase.order/purchase_piechart_detail", {
                model: "purchase.order",
                method: "purchase_piechart_detail",
                args: [total_order,paid_order,unpaid_order,waiting_bill],
                kwargs: {},
            }).then(function(res) {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);
            var options = {
              is3D:true
            };
            var chart = new google.visualization.PieChart(document.getElementById('chartContainer'));
              chart.draw(data, options);
            }
            });
            });
            });
            });
            });

rpc("/web/dataset/call_kw/sale.order/get_pending_sale_order_counts", {   //		SALE
                model: "sale.order",
                method: "get_pending_sale_order_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {

                var pending_sale_order = document.getElementById("pending_sale_order");
                if (!pending_sale_order) {
                    console.warn("pending_sale_order NOT FOUND");
                    return;
                }
                pending_sale_order.innerHTML = res;
                var sale_order = res
rpc("/web/dataset/call_kw/sale.order/get_waiting_invoice_counts", {
                model: "sale.order",
                method: "get_waiting_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                 var completed_invoice = document.getElementById("completed_invoice");
                if (!completed_invoice) {
                    console.warn("completed_invoice NOT FOUND");
                    return;
                }
                completed_invoice.innerHTML = res;
                var waiting_sale = res
rpc("/web/dataset/call_kw/account.move/get_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_unpaid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var unpaid_sale_order = document.getElementById("unpaid_sale_order");
                if (!unpaid_sale_order) {
                    console.warn("unpaid_sale_order NOT FOUND");
                    return;
                }
                unpaid_sale_order.innerHTML = res;
                var unpaid_sale = res
rpc("/web/dataset/call_kw/account.move/get_paid_invoice_counts", {
                model: "account.move",
                method: "get_paid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var paid_sale_order = document.getElementById("paid_sale_order");
                if (!paid_sale_order) {
                    console.warn("paid_sale_order NOT FOUND");
                    return;
                }
                paid_sale_order.innerHTML = res;
                var paid_sale = res
rpc("/web/dataset/call_kw/sale.order/sale_piechart_detail", {
                model: "sale.order",
                method: "sale_piechart_detail",
                args: [paid_sale,unpaid_sale,waiting_sale,sale_order],
                kwargs: {},
            }).then(function(res) {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);
            var options = {
              is3D:true
            };
            var chart = new google.visualization.PieChart(document.getElementById('chartContainer1'));
              chart.draw(data, options);
            }
            });
            });
            });
            });
            });

rpc("/web/dataset/call_kw/account.move/get_pending_invoice_counts", {   //		INVOICE
                model: "account.move",
                method: "get_pending_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {

                var pending_invoice = document.getElementById("pending_invoice");
                if (!pending_invoice) {
                    console.warn("pending_invoice NOT FOUND");
                    return;
                }
                pending_invoice.innerHTML = res;
                var total_invoice= res
rpc("/web/dataset/call_kw/account.move/get_xero_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_xero_unpaid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var unpaid_invoice = document.getElementById("unpaid_invoice");
                if (!unpaid_invoice) {
                    console.warn("unpaid_invoice NOT FOUND");
                    return;
                }
                unpaid_invoice.innerHTML = res;
                var unpaid_invoice=res
rpc("/web/dataset/call_kw/account.move/get_xero_paid_invoice_counts", {
                model: "account.move",
                method: "get_xero_paid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var paid_invoice = document.getElementById("paid_invoice");
                if (!paid_invoice) {
                    console.warn("paid_invoice NOT FOUND");
                    return;
                }
                paid_invoice.innerHTML = res;
                var paid_invoice = res
rpc("/web/dataset/call_kw/account.move/invoice_piechart_detail", {
                model: "account.move",
                method: "invoice_piechart_detail",
                args: [paid_invoice,unpaid_invoice,total_invoice],
                kwargs: {},
            }).then(function(res) {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);
            var options = {
              is3D:true
            };
            var chart = new google.visualization.PieChart(document.getElementById('chartContainer2'));
              chart.draw(data, options);
            }
            });
            });
            });
            });

rpc("/web/dataset/call_kw/account.move/get_pending_bill_counts", {   //		BILL
                model: "account.move",
                method: "get_pending_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var pending_bill = document.getElementById("pending_bill");
                if (!pending_bill) {
                    console.warn("pending_bill NOT FOUND");
                    return;
                }
                pending_bill.innerHTML = res;


                var bill_total = res
rpc("/web/dataset/call_kw/account.move/get_unpaid_xero_bill_counts", {
                model: "account.move",
                method: "get_unpaid_xero_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {

                var unpaid_bill = document.getElementById("unpaid_bill");
                if (!unpaid_bill) {
                    console.warn("unpaid_bill NOT FOUND");
                    return;
                }
                unpaid_bill.innerHTML = res;
                var unpaid = res
rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_counts", {
                model: "account.move",
                method: "get_paid_xero_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var paid_bill = document.getElementById("paid_bill");
                if (!paid_bill) {
                    console.warn("paid_bill NOT FOUND");
                    return;
                }
                paid_bill.innerHTML = res;


                var paid =res
rpc("/web/dataset/call_kw/account.move/bill_piechart_detail", {
                model: "account.move",
                method: "bill_piechart_detail",
                args: [paid,unpaid,bill_total],
                kwargs: {},
            }).then(function(res) {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);
            var options = {
              is3D:true
            };
            var chart = new google.visualization.PieChart(document.getElementById('chartContainer3'));
              chart.draw(data, options);
            }
            });
            });
            });
            });

rpc("/web/dataset/call_kw/purchase.order/get_purchase_order_details", {   //		PURCHASE
                model: "purchase.order",
                method: "get_purchase_order_details",
                args: ['last_month'],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {
                    var tr = '';
                   }
               }
		});

rpc("/web/dataset/call_kw/sale.order/get_sale_order_details", {   //		SALE
                model: "sale.order",
                method: "get_sale_order_details",
                args: ['last_month'],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {
                    var tr = '';
                   }
               }
		});

rpc("/web/dataset/call_kw/account.move/get_pending_invoice_counts", {   //		INVOICE
                model: "account.move",
                method: "get_pending_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                 var pending_invoice = document.getElementById("pending_invoice");
                if (!pending_invoice) {
                    console.warn("pending_invoice NOT FOUND");
                    return;
                }
                pending_invoice.innerHTML = res;
		});
rpc("/web/dataset/call_kw/sale.order/get_waiting_invoice_counts", {
                model: "sale.order",
                method: "get_waiting_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {

                var completed_invoice = document.getElementById("completed_invoice");
                if (!completed_invoice) {
                    console.warn("completed_invoice NOT FOUND");
                    return;
                }
                completed_invoice.innerHTML = res;
		});
rpc("/web/dataset/call_kw/account.move/get_xero_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_xero_unpaid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {

                var unpaid_invoice = document.getElementById("unpaid_invoice");
                if (!unpaid_invoice) {
                    console.warn("unpaid_invoice NOT FOUND");
                    return;
                }
                unpaid_invoice.innerHTML = res;
		});
rpc("/web/dataset/call_kw/account.move/get_xero_paid_invoice_counts", {
                model: "account.move",
                method: "get_xero_paid_invoice_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {

                var paid_invoice = document.getElementById("paid_invoice");
                if (!paid_invoice) {
                    console.warn("paid_invoice NOT FOUND");
                    return;
                }
                paid_invoice.innerHTML = res;
		});
rpc("/web/dataset/call_kw/account.move/get_invoice_details", {
                model: "account.move",
                method: "get_invoice_details",
                args: ['last_month'],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {
                    var tr = '';
                   }
               }
		});

rpc("/web/dataset/call_kw/account.move/get_pending_bill_counts", {   //		Bill
                model: "account.move",
                method: "get_pending_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var pending_bill = document.getElementById("pending_bill");
                if (!pending_bill) {
                    console.warn("pending_bill NOT FOUND");
                    return;
                }
                pending_bill.innerHTML = res;
		});
rpc("/web/dataset/call_kw/purchase.order/get_waiting_bill_counts", {
                model: "purchase.order",
                method: "get_waiting_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {

                var completed_bill = document.getElementById("completed_bill");
                if (!completed_bill) {
                    console.warn("completed_bill NOT FOUND");
                    return;
                }
                completed_bill.innerHTML = res;
		});
rpc("/web/dataset/call_kw/account.move/get_unpaid_xero_bill_counts", {
                model: "account.move",
                method: "get_unpaid_xero_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var unpaid_bill = document.getElementById("unpaid_bill");
                if (!unpaid_bill) {
                    console.warn("unpaid_bill NOT FOUND");
                    return;
                }
                unpaid_bill.innerHTML = res;
		});
rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_counts", {
                model: "account.move",
                method: "get_paid_xero_bill_counts",
                args: ['last_month'],
                kwargs: {},
            }).then(function(res) {
                var paid_bill = document.getElementById("paid_bill");
                if (!paid_bill) {
                    console.warn("paid_bill NOT FOUND");
                    return;
                }
                paid_bill.innerHTML = res;





		});
rpc("/web/dataset/call_kw/account.move/get_bill_details", {
                model: "account.move",
                method: "get_bill_details",
                args: ['last_month'],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {
                    var tr = '';
                   }
               }
		});
        }

        init() {
        this.actionManager = parent;
        return this._super.apply(this, arguments);
        }

        open_co_living_record(e) {
        }

        async on_DataType() {   //        DYNAMIC CHART
        self = this
        var element = document. getElementById('TimeData').value;
        rpc("/web/dataset/call_kw/purchase.order/get_waiting_bill_counts", {
                model: "purchase.order",
                method: "get_waiting_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var completed_bill = document.getElementById("completed_bill").innerHTML=res;
                var waiting_bill=res
        rpc("/web/dataset/call_kw/account.move/get_unpaid_bill_counts", {
                model: "account.move",
                method: "get_unpaid_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var unpaid_order = document.getElementById("unpaid_order").innerHTML=res;
                var unpaid_order=res
        rpc("/web/dataset/call_kw/account.move/get_paid_bill_counts", {
                model: "account.move",
                method: "get_paid_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var paid_order = document.getElementById("paid_order").innerHTML=res;
                var paid_order=res
        rpc("/web/dataset/call_kw/purchase.order/get_pending_order_counts", {
                model: "purchase.order",
                method: "get_pending_order_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var pending_order = document.getElementById("pending_order").innerHTML=res;
                var total_order=res
        rpc("/web/dataset/call_kw/purchase.order/purchase_piechart_detail", {
                model: "purchase.order",
                method: "purchase_piechart_detail",
                args: [total_order,paid_order,unpaid_order,waiting_bill],
                kwargs: {},
            }).then(function(res) {
			           var charttype=document.getElementById("DataType").value;
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);
   if (charttype == 'pie') {
                var options = {
                    is3D:true
                         };
                    var chart = new google.visualization.PieChart(document.getElementById('chartContainer'));
                    chart.draw(data, options);
                } else if (charttype == 'bar') {
                  var options = {
                };
                    var chart = new google.visualization.BarChart(document.getElementById('chartContainer'));
                      chart.draw(data, options);
                    } else {
                      var options = {
                      legend: 'none'
                    };
                    var chart = new google.visualization.ScatterChart(document.getElementById('chartContainer'));   // Draw
                    chart.draw(data, options);
                }
            }
        var element = document. getElementById('TimeData').value;   //      PURCHASE TABLE ON CLICK
        rpc("/web/dataset/call_kw/purchase.order/get_purchase_order_details", {
                model: "purchase.order",
                method: "get_purchase_order_details",
                args: [element],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {
                    var tr = '';
                   }
                }
		});
			});
		});
		});
		});
		   });
        }

        async on_DataType1() {
        self = this
        var element = document. getElementById('TimeData1').value;
        rpc("/web/dataset/call_kw/sale.order/get_pending_sale_order_counts", {
                model: "sale.order",
                method: "get_pending_sale_order_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var pending_sale_order = document.getElementById("pending_sale_order").innerHTML=res;
                var sale_order = res
        rpc("/web/dataset/call_kw/sale.order/get_waiting_invoice_counts", {
                model: "sale.order",
                method: "get_waiting_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var completed_invoice = document.getElementById("completed_invoice").innerHTML=res;
                var waiting_sale = res
        rpc("/web/dataset/call_kw/account.move/get_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_unpaid_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var unpaid_sale_order = document.getElementById("unpaid_sale_order").innerHTML=res;
                var unpaid_sale = res
        rpc("/web/dataset/call_kw/account.move/get_paid_invoice_counts", {
                model: "account.move",
                method: "get_paid_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var paid_sale_order = document.getElementById("paid_sale_order").innerHTML=res;
                var paid_sale = res
        rpc("/web/dataset/call_kw/sale.order/sale_piechart_detail", {
                model: "sale.order",
                method: "sale_piechart_detail",
                args: [paid_sale,unpaid_sale,waiting_sale,sale_order],
                kwargs: {},
            }).then(function(res) {
            var charttype=document.getElementById("DataType1").value;
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);
   if (charttype == 'pie') {
                var options = {
                    is3D:true
                         };
                    var chart = new google.visualization.PieChart(document.getElementById('chartContainer1'));
                    chart.draw(data, options);
                } else if (charttype == 'bar') {
                  var options = {
                };
                    var chart = new google.visualization.BarChart(document.getElementById('chartContainer1'));
                      chart.draw(data, options);
                    } else {
                      var options = {
                      legend: 'none'
                    };
                    var chart = new google.visualization.ScatterChart(document.getElementById('chartContainer1'));   // Draw
                    chart.draw(data, options);
                }
            }
		});
				});
		});
		});
		});
	    rpc("/web/dataset/call_kw/sale.order/get_sale_order_details", {
                model: "sale.order",
                method: "get_sale_order_details",
                args: [element],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {
                    var tr = '';
                   }
               }
		});
        }

        async on_DataType2() {
        self = this
        var element = document. getElementById('TimeData2').value;
        rpc("/web/dataset/call_kw/account.move/get_pending_invoice_counts", {
                model: "account.move",
                method: "get_pending_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var pending_invoice = document.getElementById("pending_invoice").innerHTML=res;
                var total_invoice= res
        rpc("/web/dataset/call_kw/account.move/get_xero_unpaid_invoice_counts", {
                model: "account.move",
                method: "get_xero_unpaid_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var unpaid_invoice = document.getElementById("unpaid_invoice").innerHTML=res;
                var unpaid_invoice=res
        rpc("/web/dataset/call_kw/account.move/get_xero_paid_invoice_counts", {
                model: "account.move",
                method: "get_xero_paid_invoice_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var paid_invoice = document.getElementById("paid_invoice").innerHTML=res;
                var paid_invoice = res
        rpc("/web/dataset/call_kw/account.move/invoice_piechart_detail", {
                model: "account.move",
                method: "invoice_piechart_detail",
                args: [paid_invoice,unpaid_invoice,total_invoice],
                kwargs: {},
            }).then(function(res) {
            var charttype=document.getElementById("DataType2").value;
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);
   if (charttype == 'pie') {
                var options = {
                    is3D:true
                         };
                    var chart = new google.visualization.PieChart(document.getElementById('chartContainer2'));
                    chart.draw(data, options);
                } else if (charttype == 'bar') {
                  var options = {
                };
                    var chart = new google.visualization.BarChart(document.getElementById('chartContainer2'));
                      chart.draw(data, options);
                    } else {
                      var options = {
                      legend: 'none'
                    };
                    var chart = new google.visualization.ScatterChart(document.getElementById('chartContainer2'));   // Draw
                    chart.draw(data, options);
                }
            }
		});
			});
		});
		});
		rpc("/web/dataset/call_kw/account.move/get_invoice_details", {
                model: "account.move",
                method: "get_invoice_details",
                args: [element],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {
                    var tr = '';
                   }
               }
		});
        }

        async on_DataType3() {
        self = this
        var element = document. getElementById('TimeData3').value;
        rpc("/web/dataset/call_kw/account.move/get_pending_bill_counts", {
                model: "account.move",
                method: "get_pending_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var pending_bill = document.getElementById("pending_bill").innerHTML=res;
                var bill_total = res
        rpc("/web/dataset/call_kw/account.move/get_unpaid_xero_bill_counts", {
                model: "account.move",
                method: "get_unpaid_xero_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var unpaid_bill = document.getElementById("unpaid_bill").innerHTML=res;
                var unpaid = res
        rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_counts", {
                model: "account.move",
                method: "get_paid_xero_bill_counts",
                args: [element],
                kwargs: {},
            }).then(function(res) {
                var paid_bill = document.getElementById("paid_bill").innerHTML=res;
                var paid =res
        rpc("/web/dataset/call_kw/account.move/bill_piechart_detail", {
                model: "account.move",
                method: "bill_piechart_detail",
                args: [paid,unpaid,bill_total],
                kwargs: {},
            }).then(function(res) {
			    var charttype=document.getElementById("DataType3").value;
			google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
            var data = google.visualization.arrayToDataTable(res);
   if (charttype == 'pie') {
                var options = {
                    is3D:true
                         };
                    var chart = new google.visualization.PieChart(document.getElementById('chartContainer3'));
                    chart.draw(data, options);
                } else if (charttype == 'bar') {
                  var options = {
                };
                    var chart = new google.visualization.BarChart(document.getElementById('chartContainer3'));
                      chart.draw(data, options);
                    } else {
                      var options = {
                      legend: 'none'
                    };
                    var chart = new google.visualization.ScatterChart(document.getElementById('chartContainer3'));   // Draw
                    chart.draw(data, options);
                }
            }
		});
		});
		});
		});
	    rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_counts", {
                model: "account.move",
                method: "get_bill_details",
                args: [element],
                kwargs: {},
            }).then(function(rec) {
                if(rec.quotation_number){
                    for (var j = 0; j < rec.quotation_number.length; j++) {
                    var tr = '';
                   }
               }
		});
        }

        async on_pending_order(){   //ON CLICK PURCHASE ORDER
        self = this
        var element = document. getElementById('TimeData').value;
          let context = this;
          rpc("/web/dataset/call_kw/purchase.order/get_purchase_id", {
                model: "purchase.order",
                method: "get_purchase_id",
                args: [element],
                kwargs: {},
            }).then(function(res) {
        self.action.doAction({
                name: _t('Purchase Order'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'purchase.order',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            });
        }

        async on_completed_order() {
        self = this
        self.action.doAction({
                name: _t('Purchase Order'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'purchase.order',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : ['&',["state", "=", "done"],["xero_purchase_id", "!=", false]],
            });
        }

        async on_paid_order() {
        var element = document. getElementById('TimeData').value;
        self = this
          let context = this;
        				rpc("/web/dataset/call_kw/account.move/get_paid_bill_id", {model:'account.move',
			           method:'get_paid_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in",res]],
            });
            	});
        }

        async on_unpaid_order() {
        var element = document. getElementById('TimeData').value;
        self = this
          let context = this;
          				rpc("/web/dataset/call_kw/account.move/get_unpaid_bill_id", {model:'account.move',
			           method:'get_unpaid_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            });
        }

        async on_completed_invoice() {   //        ON CLICK SALE ORDER
        var element = document. getElementById('TimeData1').value;
        self = this
        let context = this;
        rpc("/web/dataset/call_kw/sale.order/get_waiting_invoice_id", {model:'sale.order',
			           method:'get_waiting_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
			           localStorage.res = res;
			           self.action.doAction({
                            name: _t('Invoice'),
                            views: [[false, 'list'], [false, 'form']],
                            view_type: 'form',
                            view_mode: 'list,form',
                            res_model: 'sale.order',
                            type: 'ir.actions.act_window',
                            target: 'current',
                            domain : [["id", "=", res]],
                        });
			            });
        }

        async on_pending_sale_order() {
        var element = document. getElementById('TimeData1').value;
        self = this
        let context = this;
                rpc("/web/dataset/call_kw/sale.order/get_pending_sale_order_id", {model:'sale.order',
			           method:'get_pending_sale_order_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                 name: _t('Sale Order'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'sale.order',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            		});
        }

        async on_completed_sale_order() {
        self = this
        self.action.doAction({
                name: _t('Sale Order'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'sale.order',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : ['&',["state", "=", "done"],["xero_sale_id", "!=", false]],
            });
        }

        async on_paid_sale_order() {
        var element = document. getElementById('TimeData1').value;
        self = this
          let context = this;
        					rpc("/web/dataset/call_kw/account.move/get_paid_invoice_id", {model:'account.move',
			           method:'get_paid_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoice'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "=", res]],
            });
            		});
        }

        async on_unpaid_sale_order() {
        var element = document. getElementById('TimeData1').value;
        self = this
          let context = this;
          			    rpc("/web/dataset/call_kw/account.move/get_unpaid_invoice_id", {model:'account.move',
			           method:'get_unpaid_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoice'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            		});
        }

        async on_pending_invoice() {   //        Invoice
        var element = document. getElementById('TimeData2').value;
        self = this
          let context = this;
                      rpc("/web/dataset/call_kw/account.move/get_pending_invoice_id", {model:'account.move',
			           method:'get_pending_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoices'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            	});
        }

        async on_paid_invoice() {
        var element = document. getElementById('TimeData2').value;
        self = this
          let context = this;
        				rpc("/web/dataset/call_kw/account.move/get_xero_paid_invoice_id", {model:'account.move',
			           method:'get_xero_paid_invoice_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoice'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "=",res]],
            });
            });
        }

        async on_unpaid_invoice() {
        var element = document. getElementById('TimeData2').value;
        self = this
          let context = this;
            		   rpc("/web/dataset/call_kw/account.move/get_xero_unpaid_invoice_cid", {model:'account.move',
			           method:'get_xero_unpaid_invoice_cid',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Invoice'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in",res]],
            });
            });
        }

        async on_pending_bill() {   //        BILL
        var element = document. getElementById('TimeData3').value;
        self = this
          let context = this;
                    rpc("/web/dataset/call_kw/account.move/get_pending_bill_id", {model:'account.move',
			           method:'get_pending_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            });
        }

        async on_completed_bill() {
        var element = document. getElementById('TimeData').value;
        self = this
        let context = this;
        rpc("/web/dataset/call_kw/purchase.order/get_waiting_bill_id", {model:'purchase.order',
			           method:'get_waiting_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
			           localStorage.res = res;
			           self.action.doAction({
                            name: _t('Bill'),
                            views: [[false, 'list'], [false, 'form']],
                            view_type: 'form',
                            view_mode: 'list,form',
                            res_model: 'purchase.order',
                            type: 'ir.actions.act_window',
                            target: 'current',
                            domain : [["id", "=", res]],
                        });
			            });
        }

        async on_paid_bill() {
        var element = document. getElementById('TimeData3').value;
        self = this
          let context = this;
        				rpc("/web/dataset/call_kw/account.move/get_paid_xero_bill_id", {model:'account.move',
			           method:'get_paid_xero_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            });
        }

        async on_unpaid_bill() {
        var element = document. getElementById('TimeData3').value;
        self= this
          let context = this;
        				rpc("/web/dataset/call_kw/account.move/get_unpaid_xero_bill_id", {model:'account.move',
			           method:'get_unpaid_xero_bill_id',
			           args: [element],
			           kwargs: {},
			           }).then(function(res) {
        self.action.doAction({
                name: _t('Bill'),
                views: [[false, 'list'], [false, 'form']],
                view_type: 'form',
                view_mode: 'list,form',
                res_model: 'account.move',
                type: 'ir.actions.act_window',
                target: 'current',
                domain : [["id", "in", res]],
            });
            	});
        }
		}
registry.category("actions").add("meeting_chart", XeroDashboardViewNew);