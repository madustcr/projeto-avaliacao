import os
from flask import Flask, jsonify, request, render_template, flash, url_for, redirect
from sqlalchemy.exc import IntegrityError
from models.models import Produto, Cliente, Venda, db
from forms import ClienteForm, ProdutoForm, VendaForm
from werkzeug.utils import secure_filename
from flask_wtf.file import FileAllowed

app = Flask(__name__)

app.config['WTF_CSRF_ENABLED'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clientes.db'
app.config['SECRET_KEY'] = 'sua_chave_secreta'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')

db.init_app(app)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/adicionar-clientes', methods=['GET', 'POST'])
def adicionar_cliente():
    form = ClienteForm(data=request.form)  

    if request.method == 'POST':
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
                flash("Cliente adicionado com sucesso!", "success")
                return render_template('adicionar_clientes.html', form=form)
            except IntegrityError:
                db.session.rollback()
                flash("Erro ao adicionar cliente. CPF ou email já existente.", "danger")
                return render_template('adicionar_clientes.html', form=form)
        else:
            flash("Erro no formulário. Verifique os campos e tente novamente.", "danger")
            return render_template('adicionar_clientes.html', form=form)

    return render_template('adicionar_clientes.html', form=form)

@app.route('/adicionar-produtos', methods=['GET', 'POST'])
def add_produto():
    form = ProdutoForm()

    if request.method == 'POST':
        print("Método POST chamado.")  
        if form.validate_on_submit():
            print("Formulário validado com sucesso.")  
            if 'imagem' in request.files:
                imagem = request.files['imagem']
                if imagem.filename != '':
                    nome_imagem = secure_filename(imagem.filename)
                    caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem)

                    try:
                        imagem.save(caminho_imagem)
                        print(f"Imagem salva em {caminho_imagem}.")  
                    except Exception as e:
                        print(f"Erro ao salvar a imagem: {e}")
                        flash("Erro ao salvar a imagem. Tente novamente.", "danger")
                        return render_template('adicionar_produtos.html', form=form)

                    new_produto = Produto(
                        nome=form.nome.data,
                        preco=form.preco.data,
                        quantidade=form.quantidade.data,
                        descricao=form.descricao.data,
                        imagem=caminho_imagem
                    )

                    db.session.add(new_produto)
                    try:
                        db.session.commit()
                        flash("Produto adicionado com sucesso!", "success")
                        return render_template('adicionar_produtos.html', form=form)
                    except IntegrityError as e:
                        db.session.rollback()
                        print(f"Erro ao adicionar produto: {e}")  
                        flash("Erro ao adicionar produto. Verifique os dados e tente novamente.", "danger")
                        return render_template('adicionar_produtos.html', form=form)
                else:
                    flash("Nenhuma imagem foi enviada.", "warning")
                    return render_template('adicionar_produtos.html', form=form)
            else:
                flash("Por favor, envie uma imagem do produto.", "warning")
                return render_template('adicionar_produtos.html', form=form)
        else:
            print("Formulário inválido:", form.errors)  
            flash("Erro no formulário. Verifique os campos e tente novamente.", "danger")
            return render_template('adicionar_produtos.html', form=form)

    return render_template('adicionar_produtos.html', form=form)

@app.route('/vendas', methods=['POST'])
def add_venda():
    form = VendaForm(data=request.json)

    if form.validate():
        
        #Verificar se o cliente existe
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


@app.route('/detalhes-cliente/<int:id>', methods=['GET'])
def view_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for('get_clientes'))

    return render_template('detalhes_cliente.html', cliente=cliente)



@app.route('/detalhes-produto/<int:id>', methods=['GET'])
def view_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        flash("Produto não encontrado.", "error")
        return redirect(url_for('get_produtos'))

    # Manipula o caminho da imagem, utilizando um placeholder caso a imagem seja None
    produto_imagem = os.path.basename(produto.imagem) if produto.imagem else 'placeholder/placeholder.png'

    return render_template('detalhes_produto.html', produto=produto, produto_imagem=produto_imagem)


@app.route('/front/produtos', methods=['GET'])
def get_produtos():
    produtos = Produto.query.all()
    produtos_list = [{
        'id': produto.id,
        'nome': produto.nome,
        'preco': produto.preco,
        'quantidade': produto.quantidade,
        'descricao': produto.descricao,
        'imagem': url_for('static', filename=f'uploads/{os.path.basename(produto.imagem)}') if produto.imagem else url_for('static', filename='uploads/placeholder/placeholder.png')  # Use o placeholder se a imagem for None
    } for produto in produtos]
    return render_template('produtos.html', produtos=produtos_list)

#PAGINA DE PUT CLIENTE

@app.route('/clientes/<int:id>', methods=['GET', 'POST'])
def update_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for('/front/clientes'))

    form = ClienteForm(obj=cliente)  # Carrega dados atuais do cliente no formulário

    if request.method == 'POST':
        # Atualiza dados usando os dados enviados no formulário
        form = ClienteForm(data=request.form)

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
            flash("Cliente atualizado com sucesso!", "success")

            #DIVIDA TECNICA

            #return redirect(url_for('some_other_route'))  # GO TO HOME AFT TIMEOUT OU NAO
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Erro no campo {field}: {error}", "error")

    return render_template('editar_cliente.html', form=form, cliente_id=id)


@app.route('/produtos/<int:id>', methods=['GET', 'POST'])
def update_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        flash("Produto não encontrado.", "error")
        return redirect(url_for('get_produtos'))

    # Inicializa o formulário com os dados do produto
    form = ProdutoForm(obj=produto)

    if request.method == 'POST':
        if form.validate_on_submit():
            # Atualiza os dados do produto com os dados do formulário
            produto.nome = form.nome.data
            produto.preco = form.preco.data
            produto.quantidade = form.quantidade.data
            produto.descricao = form.descricao.data

            # Verifica se uma nova imagem foi carregada
            if 'imagem' in request.files:
                imagem = request.files['imagem']
                if imagem.filename != '':  # Verifica se a imagem foi enviada
                    nome_imagem = secure_filename(imagem.filename)
                    caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem)

                    # Tenta salvar a imagem no caminho especificado
                    try:
                        imagem.save(caminho_imagem)
                        produto.imagem = caminho_imagem  # Atualiza o caminho da imagem no banco de dados
                        print(f"Imagem salva em {caminho_imagem}.")  # Debug
                    except Exception as e:
                        print(f"Erro ao salvar a imagem: {e}")
                        flash("Erro ao salvar a imagem. Tente novamente.", "danger")
                        return render_template('editar_produto.html', form=form, produto=produto)

            # Atualiza o banco de dados com os dados do produto
            try:
                db.session.commit()
                flash("Produto atualizado com sucesso!", "success")
                return redirect(url_for('get_produtos'))  # Redireciona para a página de listagem de produtos
            except IntegrityError as e:
                db.session.rollback()
                print(f"Erro ao atualizar produto: {e}")  # Debug
                flash("Erro ao atualizar produto. Verifique os dados e tente novamente.", "danger")
                return render_template('editar_produto.html', form=form, produto=produto)

        else:
            print("Formulário inválido:", form.errors)  # Debug
            flash("Erro no formulário. Verifique os campos e tente novamente.", "danger")

    # Para GET, renderiza o template HTML do formulário
    return render_template('editar_produto.html', form=form, produto=produto, produto_id=id)


@app.route('/deletar-clientes/<int:id>', methods=['POST'])
def deletar_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        flash("Cliente não encontrado.", "error")
        return redirect(url_for('get_clientes'))  # Redireciona para a lista de clientes

        # Desvincular as vendas do cliente
    vendas = Venda.query.filter_by(cliente_id=id).all()
    for venda in vendas:
        db.session.delete(venda)  # Deleta cada venda associada ao cliente

    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente deletado com sucesso!", "success")

    return redirect(url_for('get_clientes'))

@app.route('/deletar-produto/<int:id>', methods=['POST'])
def deletar_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        flash("Produto não encontrado.", "error")
        return redirect(url_for('get_produtos'))  # Redireciona para a lista de PRODUTOS

    # Desvincular todas as vendas relacionadas ao produto
    vendas_relacionadas = Venda.query.filter_by(produto_id=id).all()
    for venda in vendas_relacionadas:
        db.session.delete(venda)

    # Agora deletar o produto
    db.session.delete(produto)
    db.session.commit()
    flash("Cliente deletado com sucesso!", "success")

    return redirect(url_for('get_produtos'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
