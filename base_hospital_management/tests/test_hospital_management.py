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
#############################################################################
from datetime import date, timedelta
from odoo import fields
from odoo.exceptions import ValidationError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHospitalManagement(TransactionCase):
    """Test suite covering hospital management workflows."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Doctor Job & Employee
        cls.doctor_job = cls.env['hr.job'].create({
            'name': 'Doctor',
        })
        cls.doctor_employee = cls.env['hr.employee'].create({
            'name': 'Dr. Robert Smith',
            'job_id': cls.doctor_job.id,
            'doctor': True,
            'time_avg': 15.0,
        })

        # Patients
        cls.patient_john = cls.env['res.partner'].create({
            'name': 'John Patient',
            'date_of_birth': date(1985, 5, 20),
            'blood_group': 'o',
            'rh_type': '+',
            'gender': 'male',
            'marital_status': 'married',
            'phone': '1234567890',
        })

        cls.patient_jane = cls.env['res.partner'].create({
            'name': 'Jane Patient',
            'date_of_birth': date(1992, 8, 15),
            'blood_group': 'a',
            'rh_type': '+',
            'gender': 'female',
            'phone': '9876543210',
        })

        # Infrastructure: Building, Ward, Room, Bed
        cls.building = cls.env['hospital.building'].create({
            'name': 'Main Clinical Block',
        })
        cls.ward = cls.env['hospital.ward'].create({
            'ward_no': 'Ward-A-101',
            'building_id': cls.building.id,
            'floor_no': 1,
        })
        cls.room = cls.env['patient.room'].create({
            'name': 'Room 101',
            'building_id': cls.building.id,
            'rent': 500.0,
            'bed_type': 'electric',
        })
        cls.bed = cls.env['hospital.bed'].create({
            'name': 'Bed-101-A',
            'ward_id': cls.ward.id,
            'room_id': cls.room.id,
            'bed_rent': 200.0,
            'bed_type': 'electric',
        })

        # Products: Medicine and Vaccine
        cls.medicine_product = cls.env['product.template'].create({
            'name': 'Paracetamol 500mg',
            'medicine_ok': True,
            'list_price': 15.0,
        })
        cls.vaccine_product = cls.env['product.template'].create({
            'name': 'Hepatitis B Vaccine',
            'vaccine_ok': True,
            'list_price': 75.0,
        })

        # Lab Test
        cls.lab_test = cls.env['lab.test'].create({
            'name': 'Complete Blood Count',
            'price': 40.0,
            'patient_lead': 2.0,
            'test_type': 'range',
        })

        # Doctor Allocation
        cls.allocation = cls.env['doctor.allocation'].create({
            'doctor_id': cls.doctor_employee.id,
            'date': fields.Date.today(),
            'work_from': 9.0,
            'work_to': 17.0,
            'state': 'confirm',
        })

    def test_01_patient_management(self):
        """Test patient creation, sequence generation, barcode, and helper actions."""
        # Check patient sequence generated
        self.assertTrue(self.patient_john.patient_seq)
        self.assertNotEqual(self.patient_john.patient_seq, 'New')

        # Test action_alive_status toggle
        self.assertEqual(self.patient_john.is_alive, 'alive')
        self.patient_john.action_alive_status()
        self.assertEqual(self.patient_john.is_alive, 'dead')
        self.patient_john.action_alive_status()
        self.assertEqual(self.patient_john.is_alive, 'alive')

        # Test generate_ean & ean_checksum
        checksum = self.patient_john.ean_checksum('123456789012')
        self.assertIsInstance(checksum, int)
        ean = self.patient_john.generate_ean(str(self.patient_john.id))
        self.assertEqual(len(ean), 13)

        # Test action_generate_patient_card (tests in-memory barcode generation)
        res = self.patient_john.action_generate_patient_card()
        self.assertTrue(res)
        self.assertTrue(self.patient_john.barcode)
        self.assertTrue(self.patient_john.barcode_png)

        # Test reception_op_barcode
        patient_data = self.env['res.partner'].reception_op_barcode({'patient_data': self.patient_john.id})
        self.assertEqual(patient_data.get('name'), self.patient_john.name)

        # Test action_view_invoice and compute
        inv_action = self.patient_john.action_view_invoice()
        self.assertEqual(inv_action.get('res_model'), 'account.move')
        self.patient_john._compute_invoice_count()
        self.assertEqual(self.patient_john.invoice_count, 0)

    def test_02_doctor_allocation_and_slots(self):
        """Test doctor allocation limits, slot calculation, and doctor slots."""
        # (17.0 - 9.0) = 8.0 hours * 60 = 480 minutes / 15.0 = 32 slots
        self.allocation._compute_patient_limit()
        self.assertEqual(self.allocation.patient_limit, 32)
        self.allocation._compute_slot_remaining()
        self.assertEqual(self.allocation.slot_remaining, 32)

        # Test validation error when work_from >= work_to
        invalid_alloc = self.env['doctor.allocation'].new({
            'doctor_id': self.doctor_employee.id,
            'work_from': 18.0,
            'work_to': 9.0,
        })
        with self.assertRaises(ValidationError):
            invalid_alloc._onchange_work_from()

        # Doctor slot workflow
        slot = self.env['doctor.slot'].create({
            'name': 'Appendectomy Consultation',
            'doctor_id': self.doctor_employee.id,
            'patient_id': self.patient_john.id,
            'date_start': fields.Datetime.now(),
            'state': 'confirmed',
        })
        confirmed_slots = slot.hospital_inpatient_confirm()
        self.assertIsInstance(confirmed_slots, list)
        slot.state = 'cancel'
        cancelled_slots = slot.hospital_inpatient_cancel()
        self.assertIsInstance(cancelled_slots, list)
        slot.state = 'done'
        done_slots = slot.hospital_inpatient_done()
        self.assertIsInstance(done_slots, list)

    def test_03_hospital_infrastructure(self):
        """Test buildings, wards, rooms, facilities, and beds."""
        facility = self.env['room.facility'].create({
            'name': 'Oxygen Concentrator',
        })
        self.room.room_facilities_ids = [(4, facility.id)]
        self.assertIn(facility, self.room.room_facilities_ids)

        # Test bed initial state
        self.assertEqual(self.bed.state, 'avail')
        self.bed.state = 'not'
        self.assertEqual(self.bed.state, 'not')
        self.bed.state = 'avail'

    def test_04_outpatient_workflow(self):
        """Test outpatient consultation creation, actions, duplicate check, and prescription lines."""
        outpatient = self.env['hospital.outpatient'].create({
            'patient_id': self.patient_john.id,
            'doctor_id': self.allocation.id,
            'op_date': fields.Date.today(),
            'reason': 'Fever and Cough',
        })
        self.assertTrue(outpatient.op_reference)

        # Duplicate OP check
        with self.assertRaises(ValidationError):
            self.env['hospital.outpatient'].create({
                'patient_id': self.patient_john.id,
                'doctor_id': self.allocation.id,
                'op_date': fields.Date.today(),
            })

        # Add prescription line
        presc_line = self.env['prescription.line'].create({
            'outpatient_id': outpatient.id,
            'medicine_id': self.medicine_product.id,
            'quantity': 10,
            'no_intakes': 1.0,
            'time': 'twice',
            'note': 'after',
        })
        self.assertIn(presc_line, outpatient.prescription_ids)

        # Confirm OP and verify slot allocation
        outpatient.action_confirm()
        self.assertEqual(outpatient.state, 'op')
        self.assertGreater(outpatient.slot, 0)

        # Test row click data helper
        row_data = self.env['hospital.outpatient'].action_row_click_data(outpatient.op_reference)
        self.assertTrue(row_data.get('op_data'))
        self.assertTrue(row_data.get('medicines'))

        # Test onchange op_date
        outpatient._onchange_op_date()

        # Test lab test action from outpatient
        lab_action = outpatient.action_create_lab_test()
        self.assertEqual(lab_action.get('res_model'), 'lab.test.line')
        self.assertEqual(lab_action.get('context', {}).get('default_patient_id'), self.patient_john.id)

        view_test_action = outpatient.action_view_test()
        self.assertEqual(view_test_action.get('res_model'), 'lab.test.line')

        # Convert to inpatient action
        conv_action = outpatient.action_convert_to_inpatient()
        self.assertEqual(conv_action.get('res_model'), 'hospital.inpatient')
        self.assertEqual(outpatient.state, 'inpatient')

        # Cancel action
        outpatient.action_op_cancel()
        self.assertEqual(outpatient.state, 'cancel')

    def test_05_inpatient_workflow(self):
        """Test inpatient admission, rent calculation, states, and surgery."""
        today = fields.Date.today()
        inpatient = self.env['hospital.inpatient'].create({
            'patient_id': self.patient_john.id,
            'attending_doctor_id': self.doctor_employee.id,
            'type_admission': 'routine',
            'room_id': self.room.id,
            'bed_id': self.bed.id,
            'hosp_date': today - timedelta(days=3),
            'discharge_date': today,
            'reason': 'Pneumonia observation',
        })
        # Compute rent amounts
        inpatient._compute_room_rent_amount()
        inpatient._compute_bed_rent_amount()
        # 4 days (3 days ago to today inclusive): Room rent 500 * 4 = 2000, Bed rent 200 * 4 = 800
        self.assertEqual(inpatient.admit_days, 4)
        self.assertEqual(inpatient.room_rent_amount, 2000.0)
        self.assertEqual(inpatient.bed_rent_amount, 800.0)

        # State transitions: Reserve -> Admit -> Discharge
        inpatient.action_reserve()
        self.assertEqual(inpatient.state, 'reserve')
        inpatient.action_admit()
        self.assertEqual(inpatient.state, 'admit')

        # Inpatient actions
        lab_action = inpatient.action_create_lab_test()
        self.assertEqual(lab_action.get('res_model'), 'lab.test.line')
        view_tests = inpatient.action_view_tests()
        self.assertEqual(view_tests.get('res_model'), 'patient.lab.test')
        view_test = inpatient.action_view_test()
        self.assertEqual(view_test.get('res_model'), 'lab.test.line')

        # Discharge
        inpatient.action_discharge()
        self.assertEqual(inpatient.state, 'dis')

        # Inpatient list and fetch helpers
        inpatient_list = self.env['hospital.inpatient'].hospital_inpatient_list()
        self.assertIsInstance(inpatient_list, list)
        fetched = self.env['hospital.inpatient'].fetch_inpatient({'patient_id': self.patient_john.id})
        self.assertIsInstance(fetched, list)

        # Test invoice view action
        inv_action = inpatient.action_view_invoice()
        self.assertEqual(inv_action.get('res_model'), 'account.move')

        # Create inpatient surgery
        surgery = self.env['inpatient.surgery'].create({
            'name': 'Appendectomy',
            'inpatient_id': inpatient.id,
            'doctor_id': self.doctor_employee.id,
            'planned_date': fields.Datetime.now(),
            'hours_to_take': 2.0,
        })
        self.assertTrue(surgery)
        surgery.action_confirm()
        self.assertEqual(surgery.state, 'confirmed')
        surgery.action_done()
        self.assertEqual(surgery.state, 'done')
        surgery.action_cancel()
        self.assertEqual(surgery.state, 'cancel')

    def test_06_laboratory_workflow(self):
        """Test laboratory, lab test ordering, confirmation, and result logging."""
        lab = self.env['hospital.laboratory'].create({
            'phone': '1122334455',
            'email': 'lab@hospital.com',
        })
        self.assertTrue(lab)

        # Create lab test line for outpatient
        lab_line = self.env['lab.test.line'].create({
            'patient_id': self.patient_john.id,
            'doctor_id': self.doctor_employee.id,
            'patient_type': 'outpatient',
            'test_ids': [(4, self.lab_test.id)],
        })
        self.assertEqual(lab_line.state, 'draft')

        # Confirm test line (creates patient.lab.test)
        lab_line.action_confirm()
        self.assertEqual(lab_line.state, 'created')

        patient_test = self.env['patient.lab.test'].search([
            ('test_id', '=', lab_line.id),
        ], limit=1)
        self.assertTrue(patient_test)
        self.assertEqual(patient_test.total_price, 40.0)

        # Start test (creates result_ids)
        self.env['patient.lab.test'].start_test(patient_test.id)
        self.assertEqual(patient_test.state, 'test')
        self.assertTrue(patient_test.result_ids)

        # Test patient_lab_test button actions & computes
        patient_test.action_start_test()
        patient_test.action_test_end()
        self.assertEqual(patient_test.state, 'completed')
        inv_action = patient_test.action_view_invoice()
        self.assertEqual(inv_action.get('res_model'), 'account.move')
        so_action = patient_test.action_view_sale_order()
        self.assertEqual(so_action.get('res_model'), 'sale.order')
        patient_test._compute_invoice_count()
        patient_test._compute_sale_count()
        patient_test._compute_medicine_ids()

        # Test print results
        results = self.env['lab.test.result'].print_test_results()
        self.assertIsInstance(results, list)

    def test_07_pharmacy_and_medicines(self):
        """Test pharmacy, medicine stock, and product helper methods."""
        brand = self.env['medicine.brand'].create({
            'name': 'PharmaCorp',
        })
        pharmacy = self.env['hospital.pharmacy'].create({
            'name': 'Central Hospital Pharmacy',
        })
        med_entry = self.env['pharmacy.medicine'].create({
            'pharmacy_id': pharmacy.id,
            'product_id': self.medicine_product.id,
        })
        self.assertIn(med_entry, pharmacy.medicine_ids)

        # Test pharmacy actions and helpers
        curr = pharmacy.company_currency()
        self.assertTrue(curr)
        inv_action = pharmacy.action_get_inventory()
        self.assertEqual(inv_action.get('res_model'), 'stock.quant')
        so_action = pharmacy.action_get_sale_order()
        self.assertEqual(so_action.get('res_model'), 'sale.order')
        so_data = pharmacy.fetch_sale_orders()
        self.assertIsInstance(so_data, list)

        # Test product template helper methods
        med_data = self.env['product.template'].action_get_medicine_data()
        self.assertIsInstance(med_data, list)
        vacc_data = self.env['product.template'].action_get_vaccine_data()
        self.assertIsInstance(vacc_data, list)

    def test_08_blood_bank_workflow(self):
        """Test blood bank donation, contraindications, and availability toggle."""
        contra = self.env['contra.indication'].create({
            'blood_donation_question': 'Have you traveled abroad in the last 30 days?',
        })
        blood_entry = self.env['blood.bank'].create({
            'partner_id': self.patient_john.id,
            'blood_type': 'o_positive',
            'date': fields.Date.today(),
        })
        # Test onchange to populate questions
        blood_entry._onchange_partner_id()
        self.assertTrue(blood_entry.blood_donation_ids)

        # Toggle state to unavailable
        self.assertEqual(blood_entry.state, 'avail')
        blood_entry.action_blood_available()
        self.assertEqual(blood_entry.state, 'not')

        # Test cron state change
        blood_entry.date = fields.Date.subtract(fields.Date.today(), months=2)
        blood_entry.action_change_availability()
        self.assertEqual(blood_entry.state, 'avail')

        # Test expand states helper
        states = blood_entry._group_expand_states([], [])
        self.assertIn('o_positive', states)

    def test_09_vaccination_workflow(self):
        """Test vaccination records and data fetching."""
        vacc = self.env['hospital.vaccination'].create({
            'patient_id': self.patient_john.id,
            'vaccine_product_id': self.vaccine_product.id,
            'vaccine_date': fields.Date.today(),
            'dose': 1.0,
        })
        self.assertTrue(vacc.name)
        self.assertNotEqual(vacc.name, 'New')

        # Test onchange next vaccine days
        vacc.next_vaccine_days = 30
        vacc._onchange_next_vaccine_days()
        self.assertEqual(vacc.next_vaccine, fields.Date.today() + timedelta(days=30))

        # Test action_create_so and action_get_sale_order
        vacc.action_create_so()
        self.assertTrue(vacc.sale_order_id)
        so_action = vacc.action_get_sale_order()
        self.assertEqual(so_action.get('res_model'), 'sale.order')

        # Test fetch vaccination data
        data = self.env['hospital.vaccination'].fetch_vaccination_data(domain=[('id', '=', vacc.id)])
        self.assertTrue(data)
        self.assertEqual(data[0]['patient_id'][0], self.patient_john.id)

    def test_10_edge_cases_and_multi_recordset(self):
        """Test multi-recordset actions, computes, and edge cases."""
        patients = self.patient_john | self.patient_jane
        patients._compute_invoice_count()
        schedule_act = self.patient_john.action_schedule()
        self.assertEqual(schedule_act.get('res_model'), 'hospital.outpatient')
        phone_data = self.env['res.partner'].reception_op_phone({'patient-phone': self.patient_john.phone})
        self.assertEqual(phone_data.get('name'), self.patient_john.name)
        p_data = self.patient_john.fetch_patient_data()
        self.assertIsInstance(p_data, list)

        # Multi-recordset for hospital beds
        beds = self.bed | self.env['hospital.bed'].create({
            'name': 'Bed-Multi-02',
            'ward_id': self.ward.id,
            'bed_rent': 250.0,
        })
        self.assertEqual(len(beds), 2)

        # Test patient display name / search
        self.assertTrue(self.patient_john.display_name)
        search_res = self.env['res.partner'].name_search('John Patient')
        self.assertTrue(search_res)
