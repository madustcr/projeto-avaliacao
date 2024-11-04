from flask import Flask, jsonify, request, render_template, url_for, redirect
from sqlalchemy.exc import IntegrityError
from models.models import Produto, Cliente, Venda, db
from forms import ClienteForm, ProdutoForm, VendaForm

app = Flask(__name__)

app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes.db'
app.config['SECRET_KEY'] = 'sua_chave_secreta'

db.init_app(app)

@app.route('/adicionar-clientes', methods=['GET', 'POST'])
def adicionar_cliente():
    if request.method == 'POST':
        form = ClienteForm(data=request.form)  # Usar `request.form` para dados de formulário

        if form.validate():
            new_cliente = Cliente(
                nome=form.nome.data,
                idade=form.idade.data,
                cpf=form.cpf.data,
                email=form.email.data,
                rua=form.rua.data,
                numero=form.numero.data,
                complemento=form.complemento.data,
                bairro=form.bairro.data,
                cidade=form.cidade.data,
                estado=form.estado.data,
                cep=form.cep.data
            )

            db.session.add(new_cliente)
            try:
                db.session.commit()
                return jsonify({"message": "Cliente adicionado com sucesso!"}), 201
            except IntegrityError:
                db.session.rollback()
                return jsonify({"error": "Erro ao adicionar cliente. CPF ou email já existente."}), 409

        return jsonify(form.errors), 400  # Retorna erros de validação do formulário
    else:
        # Carrega a página com o formulário para inserção
        return render_template('adicionar_clientes.html')


@app.route('/produtos', methods=['POST'])
def add_produto():
    form = ProdutoForm(data=request.json)

    if form.validate():
        new_produto = Produto(
            nome=form.nome.data,
            preco=form.preco.data,
            quantidade=form.quantidade.data,
            descricao=form.descricao.data,
            imagem=form.imagem.data
        )

        db.session.add(new_produto)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Erro ao adicionar produto."}), 500

        return jsonify({"message": "Produto adicionado com sucesso!"}), 201
    else:
        return jsonify(form.errors), 400  # Retorna erros de validação do formulário


@app.route('/vendas', methods=['POST'])
def add_venda():
    form = VendaForm(data=request.json)

    if form.validate():
        # Verificar se o cliente existe
        cliente = Cliente.query.get(form.cliente_id.data)
        if not cliente:
            return jsonify({"error": "Cliente não encontrado."}), 404

        # Verificar se o produto existe
        produto = Produto.query.get(form.produto_id.data)
        if not produto:
            return jsonify({"error": "Produto não encontrado."}), 404

        # Verificar se há estoque suficiente
        if produto.quantidade < form.quantidade_vendida.data:
            return jsonify({"error": "Estoque insuficiente."}), 400

        new_venda = Venda(
            cliente_id=form.cliente_id.data,
            produto_id=form.produto_id.data,
            quantidade_vendida=form.quantidade_vendida.data
        )

        produto.quantidade -= form.quantidade_vendida.data  # Atualiza a quantidade em estoque
        db.session.add(new_venda)
        db.session.commit()

        return jsonify({"message": "Venda registrada com sucesso!"}), 201
    else:
        return jsonify(form.errors), 400  # Retorna erros de validação do formulário


@app.route('/vendas', methods=['GET'])
def get_vendas():
    vendas = Venda.query.all()
    vendas_list = [{
        'id': venda.id,
        'cliente_id': venda.cliente_id,
        'produto_id': venda.produto_id,
        'quantidade_vendida': venda.quantidade_vendida
    } for venda in vendas]
    return jsonify(vendas_list), 200

# esse endpoit aqui foi so pra validar as requisicoes, o que ta retornando pro "front" é o outro

@app.route('/front/clientes', methods=['GET'])
def get_clientes():
    clientes = Cliente.query.all()
    clientes_list = [{
        'id': cliente.id,
        'nome': cliente.nome,
        'idade': cliente.idade,
        'cpf': cliente.cpf,
        'email': cliente.email,
        'rua': cliente.rua,
        'numero': cliente.numero,
        'complemento': cliente.complemento,
        'bairro': cliente.bairro,
        'cidade': cliente.cidade,
        'estado': cliente.estado,
        'cep': cliente.cep
    } for cliente in clientes]
    return render_template('clientes.html', clientes=clientes_list)


@app.route('/front/produtos', methods=['GET'])
def get_produtos():
    produtos = Produto.query.all()
    produtos_list = [{
        'id': produto.id,
        'nome': produto.nome,
        'preco': produto.preco,
        'quantidade': produto.quantidade,
        'descricao': produto.descricao,
        'imagem': produto.imagem
    } for produto in produtos]
    return render_template('produtos.html', produtos=produtos_list)

@app.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        return jsonify({"error": "Cliente não encontrado."}), 404

    form = ClienteForm(data=request.json)

    if form.validate():
        cliente.nome = form.nome.data
        cliente.idade = form.idade.data
        cliente.cpf = form.cpf.data
        cliente.email = form.email.data
        cliente.rua = form.rua.data
        cliente.numero = form.numero.data
        cliente.complemento = form.complemento.data
        cliente.bairro = form.bairro.data
        cliente.cidade = form.cidade.data
        cliente.estado = form.estado.data
        cliente.cep = form.cep.data

        db.session.commit()
        return jsonify({"message": "Cliente atualizado com sucesso!"}), 200
    else:
        return jsonify(form.errors), 400  # Retorna erros de validação do formulário


@app.route('/produtos/<int:id>', methods=['PUT'])
def update_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({"error": "Produto não encontrado."}), 404

    form = ProdutoForm(data=request.json)

    if form.validate():
        produto.nome = form.nome.data
        produto.preco = form.preco.data
        produto.quantidade = form.quantidade.data
        produto.descricao = form.descricao.data
        produto.imagem = form.imagem.data

        db.session.commit()
        return jsonify({"message": "Produto atualizado com sucesso!"}), 200
    else:
        return jsonify(form.errors), 400  # Retorna erros de validação do formulário


@app.route('/clientes/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        return jsonify({"error": "Cliente não encontrado."}), 404

    # Desvincular as vendas do cliente
    vendas = Venda.query.filter_by(cliente_id=id).all()
    for venda in vendas:
        db.session.delete(venda)  # Deleta cada venda associada ao cliente

    db.session.delete(cliente)  # Deleta o cliente
    db.session.commit()
    return jsonify({"message": "Cliente e suas vendas deletados com sucesso!"}), 204

@app.route('/produtos/<int:id>', methods=['DELETE'])
def delete_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({"error": "Produto não encontrado."}), 404

    # Desvincular todas as vendas relacionadas ao produto
    vendas_relacionadas = Venda.query.filter_by(produto_id=id).all()
    for venda in vendas_relacionadas:
        db.session.delete(venda)

    # Agora deletar o produto
    db.session.delete(produto)
    db.session.commit()
    return jsonify({"message": "Produto deletado com sucesso!"}), 204

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
