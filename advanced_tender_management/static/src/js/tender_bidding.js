/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.TenderBiddingForm = publicWidget.Widget.extend({
    selector: '.tender_details_page',
    events: {
        'change .vendor_bid': '_onChangeComputeTotal',
        'click .edit-request-btn': '_onClickEditRequest',
        'change #att': '_onChangeFileInput',
        'submit .tender-bid-form': '_onSubmitBidForm',
    },
    _onChangeFileInput: function(ev) {
        var fileInput = ev.target;
        var fileNameDisplay = this.el.querySelector('.file-name-display');
        var errorAlert = this.el.querySelector('.doc-upload-error');
        if (fileInput.files && fileInput.files.length > 0) {
            var fileName = fileInput.files[0].name;
            if (fileNameDisplay) {
                fileNameDisplay.innerHTML = `<i class="fa fa-check-circle text-success me-1"></i> <strong class="text-success">${fileName}</strong>`;
            }
            if (errorAlert) {
                errorAlert.classList.add('d-none');
            }
        } else {
            if (fileNameDisplay) {
                fileNameDisplay.textContent = '';
            }
        }
    },
    _onSubmitBidForm: function(ev) {
        var fileInput = this.el.querySelector('#att');
        var errorAlert = this.el.querySelector('.doc-upload-error');
        var allProductRows = this.el.querySelectorAll('.product_row');

        // Check if document is selected
        if (fileInput && (!fileInput.files || fileInput.files.length === 0)) {
            ev.preventDefault();
            if (errorAlert) {
                errorAlert.classList.remove('d-none');
            }
            fileInput.closest('.doc-file-upload').scrollIntoView({ behavior: 'smooth', block: 'center' });
            return false;
        }

        // Ensure product bid list is always compiled
        $('.hidden_price_input').remove();
        var productList = Array.from(allProductRows).map(row => {
            var inputElement = row.querySelector('.vendor_bid');
            var productId = inputElement.getAttribute('product_id');
            var value = inputElement.value || 0;
            return [productId, value];
        });
        $('.tender-bid-form').append(`<input type="hidden" class="hidden_price_input" name="product_bid_list" value='${JSON.stringify(productList)}'>`);
    },
    _onClickEditRequest: async function(ev) {
        var value = $('.bid_info').attr('data-bid_id');
        await rpc('/edit_request', {'bid_id': value}).then((result) => {
            window.location.href = '/edit_request_success';
        });
    },
    _onChangeComputeTotal: async function(ev) {
        $('.hidden_price_input').remove();
        var targetRow = ev.target.closest('tr');
        var vendor_price = ev.target.value;
        var product_qty = targetRow.querySelector('.product_qty').textContent.replace(',', '');
        var total_price = parseInt(product_qty) * parseFloat(vendor_price);
        targetRow.querySelector('.total_price').textContent = total_price.toFixed(2);
        var grandTotal = 0;
        var allProductRows = ev.target.closest('tbody').querySelectorAll('.product_row');
        var productList = Array.from(allProductRows).map(row => {
            var inputElement = row.querySelector('.vendor_bid');
            var productId = inputElement.getAttribute('product_id');
            var value = inputElement.value;
            var qty = parseFloat(row.querySelector('.product_qty').textContent.replace(',', '')) || 0;
            var rowTotalPrice = qty * value;
            grandTotal += rowTotalPrice;
            return [productId, value];
        });
        var totalRow = ev.target.closest('tbody').querySelector('.total_row .grand_total');
        if (totalRow) {
            totalRow.textContent = grandTotal.toFixed(2);
        }
        $('.tender-bid-form').append(`<input type="hidden" class="hidden_price_input" name="product_bid_list" value='${JSON.stringify(productList)}'>`);
    }
});
