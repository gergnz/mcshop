from flask import Blueprint, render_template, redirect, url_for, request, flash, Response, _app_ctx_stack
from flask_table import Table, Col, ButtonCol
import docker
from .utils import otp_required, ModalCol, Modal2Col

container = Blueprint('container', __name__)

def flask_logger(containerid):
    """creates logging information"""
    client = docker.from_env()
    cont = client.containers.get(containerid)
    for i in cont.logs(stream=True, tail=30):
        yield i

@container.route('/containers')
@otp_required
def containers():
    client = docker.from_env()
    allcontainers = client.containers.list(all=True)

    for cont in allcontainers:
        if cont.name == 'mcshop':
            allcontainers.remove(cont)

    token=_app_ctx_stack.top._csrf_token #pylint: disable=protected-access

    class ContainerTable(Table):
        status = Col('Status')
        image = Col('Image')
        name = Col('Name')
        delete = ModalCol(
            'Delete',
            'container.containermgt',
            url_kwargs=dict(id='id'),
            url_kwargs_extra=dict(task='delete'),
            button_attrs={'class': 'btn btn-danger btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#deleteModal'}
        )
        stop = ButtonCol(
            'Stop',
            'container.containermgt',
            url_kwargs=dict(id='id'),
            url_kwargs_extra=dict(task='stop'),
            form_hidden_fields=dict(_csrf_token=token),
            button_attrs={'class': 'btn btn-warning btn-sm', 'data-bs-toggle': "modal", 'data-bs-target': "#waitModal"}
        )
        start = ButtonCol(
            'Start',
            'container.containermgt',
            url_kwargs=dict(id='id'),
            url_kwargs_extra=dict(task='start'),
            form_hidden_fields=dict(_csrf_token=token),
            button_attrs={'class': 'btn btn-success btn-sm', 'data-bs-toggle': "modal", 'data-bs-target': "#waitModal"}
        )
        logs = Modal2Col(
            'Logs',
            '',
            url_kwargs=dict(id='id'),
            button_attrs={'class': 'btn btn-secondary btn-sm', 'data-bs-toggle': 'modal', 'data-bs-target': '#logsModal'}
        )
        classes = ['table', 'table-striped', 'table-bordered', 'bg-light']
        html_attrs = dict(cellspacing='0')
        table_id = 'allcontainers'

    table = ContainerTable(allcontainers)
    return render_template('containers.html', allcontainers=table.__html__(),)

@container.route('/containermgt', methods=['POST'])
@otp_required
def containermgt():
    container_id = request.args.get('id')
    task = request.args.get('task')

    client = docker.from_env()

    cont = client.containers.get(container_id)

    try:
        if task == 'stop':
            cont.stop()
            flash("Container stopped successfully.", "success")
        if task == 'start':
            cont.start()
            flash("Container started successfully.", "success")
        if task == 'delete':
            cont.stop()
            cont.wait()
            cont.remove()
            flash("Container deleted successfully.", "success")
    except Exception as error: #pylint: disable=broad-except
        flash(f"Container operation failed: {error}", "danger")

    return redirect(url_for('container.containers'))

@container.route("/log_stream/<containerid>", methods=["GET"])
@otp_required
def stream(containerid):
    """returns logging information"""
    return Response(flask_logger(containerid), mimetype="text/plain", content_type="text/event-stream")
