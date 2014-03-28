# -*- coding: utf-8 -*-

from osv import osv
from osv import fields
import decimal_precision as dp
import time

##
#	El orden de los estados en esta lista determina el orden en
#	que se presentan en la vista.
##

class solicitud_recursos(osv.osv):
	_inherit = "mail.thread"
	_name="solicitud.recursos"

	LISTA_ESTADOS_SOLICITUD = [
		('draft', 'Nuevo'),
		('sent_to_approval', 'En aprobación'),
		('approved', 'Aprobado'),
		('rejected', 'Rechazado'),
		('closed_total', 'Cumplimiento total'),
		('closed_partial', 'Cumplimiento parcial'),
		#('purchase_request', 'A comprar' ),
	]
	
	def _get_company_id(self, cr, uid, context=None):
		res = self.pool.get('res.users').read(cr, uid, [uid], ['company_id'], context=context)
		if res and res[0]['company_id']:
			return res[0]['company_id'][0]
		return False

	def _get_user_id(self, cr, uid, context=None):
		"""
		If the user is logged in (i.e. not anonymous), get the user's name to
		pre-fill the partner_name field.
		Same goes for the other _get_user_attr methods.

		@return current user's name if the user isn't "anonymous", None otherwise
		"""
		user_id = self.pool.get('res.users').read(cr, uid, uid, ['id'], context)

		return user_id['id']
		
	def _get_user_name(self, cr, uid, context=None):
		"""
		If the user is logged in (i.e. not anonymous), get the user's name to
		pre-fill the partner_name field.
		Same goes for the other _get_user_attr methods.

		@return current user's name if the user isn't "anonymous", None otherwise
		"""
		user = self.pool.get('res.users').read(cr, uid, uid, ['login'], context)

		if (user['login'] != 'anonymous'):
			return self.pool.get('res.users').name_get(cr, uid, uid, context)[0][1]
		else:
			return None

	_columns = {
		'inciso':fields.char ('Inciso'),
		'u_e': fields.char ('UE'),
		'name': fields.char ( 'Solicitud', size = 32, required = True ), # Nro Solicitud
#		'origin': fields.char ( 'Documento orígen', size = 32 ),
		'date_start': fields.date ( 'Fecha de solicitud' ), # Fecha de solicitud
		'description': fields.char ( 'Descripción', size= 10),
		'user_id': fields.many2one ( 'res.users', 'Solicitante' ), # Solicitante
		'srl_ids_solicitado' : fields.one2many ( 'solicitud.recursos.line', 'sr_solicitud_id', 'Productos solicitados' ),
		'state': fields.selection ( LISTA_ESTADOS_SOLICITUD, 'Estado', size = 20, readonly = True ),
		'user_id':fields.many2one('res.users', 'Solicitante'),
		'company_id': fields.many2one ( 'res.company', 'Compañía'), # Compañía
		'company_id': fields.many2one ( 'res.company','Compañía' ),
		'warehouse':fields.many2one('stock.warehouse','Centro de almacenaje'), #encontrar la clase almacen de openerp para relacionarla

		######################## Estados ####################################
	}
	def action_estado_cerrado(self, cr, uid, ids, values, context=None):
         subject = 'Cambio de estado a Cerrado'

         cr.execute("""  select partner_id from res_users where id = %s""",
                     (uid,))
         cli = cr.fetchone()[0]

         message = self.pool.get('mail.message')
         message.create(cr, uid, {
                 'res_id': ids[0],
                 'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                 'author_id': cli,
                 'model': self._name,
                 'subject' : subject,
                 'body': values
             }, context=context)
         self.write(cr, uid, ids, {'state': 'cerrado', 'fechacierre': 
		time.strftime('%Y-%m-%d %H:%M:%S')})
         return True
	
	############ Senhal ###########
	def action_Solicitar_Aprobacion(self, cr, uid, ids, context=None):
		self.write(cr,uid,ids,{'state':'sent_to_approval'},context)
		return True

	############ Senhal ###########
	def action_Consultar_Stock(self, cr, uid, ids, context=None):
		self.write(cr,uid,ids,{'state':'approved'},context)
		return True

	############ Senhal ###########
	def action_Rechazado(self, cr, uid, ids, context=None):
		self.write(cr,uid,ids,{'state':'rejected'},context)
		return True

	############ Senhal ###########
	def action_Sr_Cerrada(self, cr, uid, ids, context=None):
		self.write(cr,uid,ids,{'state':'closed_total'},context)
		return True

	############ Senhal ###########
	def action_Cumple_Parcial(self, cr, uid, ids, context=None):
		self.write(cr,uid,ids,{'state':'closed_partial'},context)
		return True

	############ Senhal ###########
	"""def action_Para_Compras ( self, cr, uid, ids, context = None ):
		self.write ( cr, uid, ids, { 'state' : 'purchase_request' }, context )
		return True"""

	_defaults = {
		'inciso' : '06',
		'u_e' : '001',
		'state' : 'draft',
		'name' : lambda obj, cr, uid, context: obj.pool.get ( 'ir.sequence' ).get ( cr, uid, 'resource.requisition.number' ),
		'company_id': _get_company_id,
		'user_id': _get_user_id,
		'date_start': time.strftime('%Y-%m-%d'),
	}	

class solicitud_recursos_line ( osv.osv ):

	_name = "solicitud.recursos.line"
	_description="Lineas de Pedidos Custom"
	_rec_name = 'product_id'

	LISTA_ESTADOS_LINEA_SOLICITUD = [
		('noe', 'No entregado'),
		('noh', 'No hay'),
		('total', 'Entregado Total'),
		('parcial', 'Entregado Parcial'),
		('acompra', 'Enviado a compra'),
	]
	
	def onchange_product_id(self, cr, uid, ids, product_id, product_uom_id, context=None):
                """ Changes UoM and name if product_id changes.
                @param name: Name of the field
                @param product_id: Changed product_id
                @return:  Dictionary of changed values
                """
                value = {'product_uom_id': ''}
                if product_id:
                        prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
                        value = {'product_uom_id': prod.uom_id.id,'product_requested_qty':1.0}
                return {'value': value}
                
	             

	def _get_uom_id(self, cr, uid, *args):
		cr.execute('select id from product_uom order by id limit 1')
		res = cr.fetchone()
		return res and res[0] or False

	_columns = {
		'product_id': fields.many2one ('product.product', 'Producto' ), # Producto
		'product_uom_id': fields.many2one('product.uom', 'UdM', readonly=True),
		'product_requested_qty': fields.float ( 'Cant Requerida', digits_compute=dp.get_precision('Unidad de medida')),
		'sr_solicitud_id' : fields.many2one('solicitud.recursos','Solicitado', ondelete='cascade'),
		'state': fields.related ( 'sr_solicitud_id', 'state', type = 'char', readonly=True ),
		'precio': fields.char('Precio', readonly=True), #cuando este la relacion va many2one a 'pricelist.partnerinfo'
		'product_date_need':fields.date('Fecha de necesidad'),
		'product_purchase_order':fields.char('Orden de compra', readonly=True),
		'comentarios': fields.text ( 'Comentarios', size = 30 ),
		'estado': fields.selection ( LISTA_ESTADOS_LINEA_SOLICITUD, 'Status entrega', size = 20, readonly = True ),
		'num_entrega': fields.char ('N Entrega'),
		'cant_engregada': fields.char ('Cant Entregada'),
		'O/C': fields.char ('O/C'),
	}

	defaults = {
		'product_uom_id': _get_uom_id,
	}
