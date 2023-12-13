from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import Laptop as LaptopModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'harga': 7, 'ram': 4, 'kapasitas_baterai': 3, 'processor': 4, 'penyimpanan_internal': 2}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(LaptopModel.id_laptop, LaptopModel.harga, LaptopModel.ram, LaptopModel.kapasitas_baterai, LaptopModel.processor, LaptopModel.penyimpanan_internal)
        result = session.execute(query).fetchall()
        print(result)
        return [{'id_laptop': laptop.id_laptop, 'harga': laptop.harga, 'ram': laptop.ram, 'kapasitas_baterai': laptop.kapasitas_baterai, 'processor': laptop.processor, 'penyimpanan_internal': laptop.penyimpanan_internal} for laptop in result]

    @property
    def normalized_data(self):
        harga_values = []
        ram_values = []
        kapasitas_baterai_values = []
        processor_values = []
        penyimpanan_internal_values = []

        for data in self.data:
            harga_values.append(data['harga'])
            ram_values.append(data['ram'])
            kapasitas_baterai_values.append(data['kapasitas_baterai'])
            processor_values.append(data['processor'])
            penyimpanan_internal_values.append(data['penyimpanan_internal'])

        return [
            {'id_laptop': data['id_laptop'],
             'harga': min(harga_values) / data['harga'],
             'ram': data['ram'] / max(ram_values),
             'kapasitas_baterai': data['kapasitas_baterai'] / max(kapasitas_baterai_values),
             'processor': data['processor'] / max(processor_values),
             'penyimpanan_internal': data['penyimpanan_internal'] / max(penyimpanan_internal_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['harga'] ** self.raw_weight['harga'] *
                row['ram'] ** self.raw_weight['ram'] *
                row['kapasitas_baterai'] ** self.raw_weight['kapasitas_baterai'] *
                row['processor'] ** self.raw_weight['processor'] *
                row['penyimpanan_internal'] ** self.raw_weight['penyimpanan_internal']
            )

            produk.append({
                'id_laptop': row['id_laptop'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'id_laptop': product['id_laptop'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['id_laptop']:
                  round(row['harga'] * weight['harga'] +
                        row['ram'] * weight['ram'] +
                        row['kapasitas_baterai'] * weight['kapasitas_baterai'] +
                        row['processor'] * weight['processor'] +
                        row['penyimpanan_internal'] * weight['penyimpanan_internal'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class Laptop(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(LaptopModel)
        data = [{'id_laptop': laptop.id_laptop, 'harga': laptop.harga, 'ram': laptop.ram, 'kapasitas_baterai': laptop.kapasitas_baterai, 'processor': laptop.processor, 'penyimpanan_internal': laptop.penyimpanan_internal} for laptop in session.scalars(query)]
        return self.get_paginated_result('laptop/', data, request.args), HTTPStatus.OK.value


api.add_resource(Laptop, '/laptop')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
