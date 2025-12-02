# routes/producto.py
from flask import Blueprint, request, jsonify
from models.area import Area

ws_area = Blueprint('ws_area', __name__)
modelo = Area()

@ws_area.route('/Listarareas', methods=['GET'])
def obtener_areas():
    areas = modelo.ListarArea()
    if areas is not None:
        return jsonify(areas), 200
    else:
        return jsonify({"mensaje": "Error al obtener areas"}), 500

# ==================== ENDPOINTS PARA MANTENIMIENTO ====================

@ws_area.route('/areas/mantenimiento', methods=['GET'])
def obtener_areas_mantenimiento():
    """Obtener todas las áreas para mantenimiento"""
    try:
        areas = modelo.ListarArea()
        if areas is not None:
            return jsonify({
                'status': True,
                'mensaje': 'Áreas obtenidas exitosamente',
                'areas': areas
            }), 200
        else:
            return jsonify({
                'status': False,
                'mensaje': 'Error al obtener áreas',
                'areas': []
            }), 500
    except Exception as e:
        return jsonify({
            'status': False,
            'mensaje': f'Error: {str(e)}',
            'areas': []
        }), 500

@ws_area.route('/area/agregar', methods=['POST'])
def agregar_area():
    """Agregar una nueva área desde mantenimiento"""
    try:
        data = request.get_json()
        
        if not data or 'nombre_area' not in data:
            return jsonify({'mensaje': 'nombre_area es requerido'}), 400
        
        nombre_area = data['nombre_area'].strip()
        
        if not nombre_area:
            return jsonify({'mensaje': 'El nombre del área no puede estar vacío'}), 400
        
        # Verificar si el área ya existe
        if modelo.ExisteArea(nombre_area):
            return jsonify({'mensaje': 'El área ya existe'}), 409
        
        id_area = modelo.CrearArea(nombre_area)
        
        if id_area:
            return jsonify({
                'mensaje': 'Área agregada exitosamente',
                'id_area': id_area
            }), 201
        else:
            return jsonify({'mensaje': 'Error al agregar área'}), 500
            
    except Exception as e:
        return jsonify({'mensaje': f'Error interno: {str(e)}'}), 500

@ws_area.route('/area/editar/<int:id_area>', methods=['PUT'])
def editar_area(id_area):
    """Editar un área existente"""
    try:
        data = request.get_json()
        
        if not data or 'nombre_area' not in data:
            return jsonify({'mensaje': 'nombre_area es requerido'}), 400
        
        nombre_area = data['nombre_area'].strip()
        
        if not nombre_area:
            return jsonify({'mensaje': 'El nombre del área no puede estar vacío'}), 400
        
        # Verificar si el área existe
        if not modelo.ExisteAreaById(id_area):
            return jsonify({'mensaje': 'El área no existe'}), 404
        
        # Verificar si el nuevo nombre ya existe (excluyendo el área actual)
        if modelo.ExisteAreaExceptoId(nombre_area, id_area):
            return jsonify({'mensaje': 'Ya existe otra área con ese nombre'}), 409
        
        resultado = modelo.EditarArea(id_area, nombre_area)
        
        if resultado:
            return jsonify({'mensaje': 'Área actualizada exitosamente'}), 200
        else:
            return jsonify({'mensaje': 'Error al actualizar área'}), 500
            
    except Exception as e:
        return jsonify({'mensaje': f'Error interno: {str(e)}'}), 500

@ws_area.route('/area/eliminar/<int:id_area>', methods=['DELETE'])
def eliminar_area(id_area):
    """Eliminar un área"""
    try:
        # Verificar si el área existe
        if not modelo.ExisteAreaById(id_area):
            return jsonify({'mensaje': 'El área no existe'}), 404
        
        # Verificar si el área tiene salidas asociadas
        if modelo.TieneSalidasAsociadas(id_area):
            return jsonify({
                'mensaje': 'No se puede eliminar el área porque tiene salidas asociadas'
            }), 409
        
        resultado = modelo.EliminarArea(id_area)
        
        if resultado:
            return jsonify({'mensaje': 'Área eliminada exitosamente'}), 200
        else:
            return jsonify({'mensaje': 'Error al eliminar área'}), 500
            
    except Exception as e:
        return jsonify({'mensaje': f'Error interno: {str(e)}'}), 500