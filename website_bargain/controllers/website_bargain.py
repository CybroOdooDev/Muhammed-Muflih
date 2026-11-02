# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteAuction(WebsiteSale):
    """This class enables is used to view the timer and related functions
        of bidding,buy now and other routes
        _prepare_product_values(self, product, category, search, **kwargs):
                This function is inbuilt function in website sale and its
                supered here and pass auction values in this function
        auction_timer(self, auction_id):
                This function gets the auction id and pass auction timing
                details to website
        buy_now(self, auction_id, product_id):
                Its the function for button in buy now,in this function a new
                sale order is created and send to the customer through email
        def auction_close(self, auction_id):
                Function gets the auction id and move the auction stage to
                finished and make the product unavailable from website
        winner_sale_order(self, auction_id, **post):
                Makes a sale order to the winner and id notifications are
                enabled it will send a email to the winners or losers
        subscribe(self, auction_id, **post):
                Used to add subscribers from website to database
        place_bid(self, auction_id, **post):
                When place bid button is triggered it will call this function
                 and the bidders details will be added to database and
                  if enabled it will send notification to subscribers
        bidders(self, product_id):
                Route to pass bidders details to website
        bid_cancel(self, bidders):
                Function to cancel the bid"""

    def _prepare_product_values(self, product, **kwargs):
        """
        Extends website_sale.product rendering context with auction data.
        """
        # Get parent dictionary
        values = super()._prepare_product_values(product, **kwargs)

        # Ensure required base variables exist
        values.setdefault('image_cols', [5, 7])  # template expects this

        # Add custom auction logic
        current_website = getattr(request.env, 'website', False) or request.env['website'].search([], limit=1)
        domain = [
            ('product_id', '=', product.id),
            ('state', '=', 'running'),
        ]
        if current_website:
            domain.append(('website_id', 'in', (current_website.id, False)))
        auction = request.env['website.bargain'].sudo().search_read(domain)
        values.update({
            'auction': auction,
            'website': current_website,
        })
        return values

    @http.route('/auction/timer', type='jsonrpc', auth='user', csrf=False)
    def auction_timer(self, auction_id):
        """Summary:
                Function to pass timer details from auction like start
                 time,end time,extended time
            Args:
                auction_id:used to get auction id from website
            Return:
                Values which include start_time,end time,extended
                 time and state id"""
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        values = {
            'start_time': fields.Datetime.context_timestamp(auction,
                                                          auction.start_time),
            'end_time': fields.Datetime.context_timestamp(auction,
                                                          auction.end_time),
            'state': auction.state,
        }
        if auction.extend_time:
            values['extend_time'] = fields.Datetime.context_timestamp(auction,
                                                                      auction.extend_time)
        return values

    @http.route('/auction/close', type='jsonrpc', auth='user', csrf=False)
    def auction_close(self, auction_id, **post):
        """Summary:
            Function to close auction when a customer buys
            a product instantly or the auction is ended
        Args:
            auction_id: used to get auction id from website
        Return:
            a string auction ended to website"""
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        if not auction.exists():
            return "auction not found"

        is_manager = (
            auction.auction_manager_id == request.env.user or
            request.env.user.has_group('base.group_system')
        )
        now = fields.Datetime.now()
        effective_end = auction.extend_time or auction.end_time
        is_expired = effective_end and effective_end <= now

        if not (is_manager or is_expired):
            return "Unauthorized"

        auction._process_auction_end()
        return "auction ended"

    @http.route('/place_bid', type='jsonrpc', auth='user', csrf=False)
    def place_bid(self, auction_id, **post):
        """Summary:
                When place bid button is clicked it will trigger this function
                 and will add bidders details to backend and will send
                 notification to the subscribers if its enabled
            Args:
                auction_id: used to get auction id from website
                post: used to get bid amount from frontend
            Return:
                A message bid placed and auction details"""
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        if not auction.exists() or auction.state != 'running':
            return False

        # Server-side validation: check if auction has expired
        now = fields.Datetime.now()
        effective_end = auction.extend_time or auction.end_time
        if effective_end and effective_end <= now:
            return False

        # Server-side validation: bid amount
        try:
            bid_amount = float(post.get('bid_amount'))
        except (ValueError, TypeError):
            return False

        if bid_amount <= 0 or bid_amount <= auction.initial_price:
            return False

        placed_bids = auction.bargain_information_ids.filtered(
            lambda r: r.status == 'Bid Placed'
        )
        if placed_bids:
            highest_bid = max(placed_bids.mapped('bid_offer'))
            if bid_amount <= highest_bid:
                return False

        bidder_total = auction.bargain_information_ids.search_count(
            [('bidder_id', '=', request.env.user.partner_id.id),
             ('bid_offer', '=', bid_amount),
             ('auction_id', '=', auction.id)])
        if bidder_total >= 1:
            return False

        auction.bargain_information_ids.sudo().create({
            'bidder_id': request.env.user.partner_id.id,
            'auction_id': auction.id,
            'bid_offer': bid_amount,
            'status': 'Bid Placed'
        })
        if auction.is_subscriber_start_notification and not auction.is_send_mail:
            data = f"Bidding has started for {auction.name or ''}. Please check our website for more details."
            subscribers = ','.join(s.subscriber_id.email for s in auction.bargain_subscribers_ids if s.subscriber_id.email)
            if subscribers and auction.auction_manager_id.email:
                email_values = {'email_from': auction.auction_manager_id.email,
                                'subject': 'Bidding Started for ' + (auction.name or ''),
                                'email_to': subscribers, 'body_html': data}
                request.env['mail.mail'].sudo().create(email_values).send()
                auction.write({'is_send_mail': True})

        if auction.is_new_bid_notification:
            partner_name = request.env.user.partner_id.name or ''
            data = (
                f"A new bid of {bid_amount} has been placed on {auction.name or ''} "
                f"by {partner_name}. Please check our website for details."
            )
            subscribers = ','.join(s.subscriber_id.email for s in auction.bargain_subscribers_ids if s.subscriber_id.email)
            if subscribers and auction.auction_manager_id.email:
                email_values = {'email_from': auction.auction_manager_id.email,
                                'subject': 'New Bid Placed on ' + (auction.name or ''),
                                'email_to': subscribers, 'body_html': data}
                request.env['mail.mail'].sudo().create(email_values).send()
        values = ({
            'bid_placed': 'Bid Placed',
            'auction': auction
        })

        return values

    @http.route('/bidders/<model("product.template"):product_id>', type='http',
                auth='user', csrf=False, website=True)
    def bidders(self, product_id):
        """
        This method is used to fetch the details of the bidders participating in
         an auction and render them on the website.
        Args:
            product_id: A product template model object.
        Returns:
            A rendered HTML template with information about the bidders in the
            auction."""
        auction = request.env['website.bargain'].sudo().search(
            [('product_id', '=', product_id.id), ('state', '=', 'running')])
        bidders_information = request.env['bargain.information'].sudo().search(
            [('auction_id', '=', auction.id)],
            order='bid_offer desc')
        values = ({
            'bidders_information': bidders_information,
            'product_id': product_id,
            'auction': auction,
        })
        return request.render('website_bargain.bidders_information', values)

    @http.route('/bid/cancel/<model("bargain.information"):bidders>',
                type='http', auth='user', csrf=False)
    def bid_cancel(self, bidders):
        """This function is for cancel the bid
            Args:
                bidders: Bidders record to cancel
            Returns: Redirects to previous page"""
        is_owner = bidders.bidder_id == request.env.user.partner_id
        is_manager = (
            bidders.auction_id.auction_manager_id == request.env.user or
            request.env.user.has_group('base.group_system')
        )
        if is_owner or is_manager:
            bidders.sudo().write({'status': 'cancelled'})
        previous_web_url = request.httprequest.headers.get('referer') or '/shop'
        return request.redirect(previous_web_url)

    @http.route('/shop/sale/order', type='jsonrpc', auth='user', website=True,
                csrf=False)
    def winner_sale_order(self, auction_id, **post):
        """
            This route creates a draft sale order for the winner of an auction
            and sends notifications for winning and losing.
        Args:
            auction_id: the ID of the auction obtained from the frontend
            post: used to get data of product from frontend
        Returns:
            True"""
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        if not auction.exists():
            return False

        is_manager = (
            auction.auction_manager_id == request.env.user or
            request.env.user.has_group('base.group_system')
        )
        now = fields.Datetime.now()
        effective_end = auction.extend_time or auction.end_time
        is_expired = bool(effective_end and effective_end <= now)
        if not (is_manager or is_expired):
            return False

        if auction.state == 'running':
            auction._process_auction_end()
        return True

    @http.route('/subscribe/bid', type='jsonrpc', auth='user', csrf=False)
    def subscribe(self, auction_id, **post):
        """
        Endpoint to manage subscription to an auction
         auction_id: integer ID of the auction being subscribed to/unsubscribed
         text: string indicating whether the user is subscribing or
         unsubscribing ('subscribe' or 'unsubscribe')
        return: string message indicating success or failure of
        subscription/unsubscription action
        """
        text = post.get('text')
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        if text == 'subscribe':
            if request.env.user.partner_id in \
                    auction.bargain_subscribers_ids.subscriber_id:
                return 'You have already subscribed'
            auction.bargain_subscribers_ids.sudo().create({
                'subscriber_id': request.env.user.partner_id.id,
                'auction_id': auction.id,
                'is_subscribed': True
            })
            return 'You have been successfully subscribed to this auction'
        elif text == 'unsubscribe':
            auction.bargain_subscribers_ids.sudo().search(
                [('subscriber_id', '=', request.env.user.partner_id.id),
                 ('auction_id', '=', auction.id)]).unlink()
            return 'Unsubscribed successfully'

    @http.route('/subscribe/status', type='jsonrpc', auth='user', csrf=False)
    def subscribe_status(self, auction_id,  **post):
        """
        Controller method to handle subscription to an auction.
        """
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        is_subscribed = False
        for subscriber in auction.bargain_subscribers_ids:
            if subscriber.subscriber_id == request.env.user.partner_id:
                is_subscribed = subscriber.is_subscribed
                break

        return is_subscribed

    @http.route('/buy/now', type='jsonrpc', auth='user', website=True,
                csrf=False)
    def buy_now(self, auction_id, product_id, **post):
        """
        Args:
            auction_id: the ID of the auction obtained from the frontend
            product_id: the ID of the product used to get data from the frontend
        """
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        if not auction.exists() or auction.state != 'running' or not auction.is_buy_now:
            return False

        product = request.env['product.product'].sudo().browse(int(product_id))
        if not product.exists() or product.product_tmpl_id != auction.product_id:
            return False

        # Create a draft sale order for the winner
        sale_order = request.env['sale.order'].sudo().create({
            'partner_id': request.env.user.partner_id.id,
            'state': 'draft',
        })
        sale_order.sudo().write({
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
                'name': '(auction won) ' + (auction.name or ''),
                'price_unit': auction.price_buy_now,
            })]
        })
        # Send a notification email to the winner
        mail_compose_message = request.env['mail.compose.message']
        so_mcm_vals = sale_order.sudo().action_quotation_send().get('context',
                                                                    {})
        compose_msg = mail_compose_message.sudo().with_context(
            so_mcm_vals).create({})
        compose_msg.sudo().action_send_mail()

        # Mark auction finished upon instant buy
        auction.write({'state': 'finished'})
        auction.product_id.is_auction = False
        auction.product_id.is_published = False
        return True
