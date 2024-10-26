# Django-Bibliotheken
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType



# Lokale Module
from ...models import (
    Thread,
    User,
    Comment,
    SharedQuestion,
    ReportModel
)
from ...schema import (
    ReportPayload
)

class ReportReciever:
    @staticmethod
    def create_report(user: User, payload: ReportPayload):
        model_mapping = {
            'thread': Thread,
            'comment': Comment,
            'shared_question': SharedQuestion
        }

        model_id_mapping = {
            'thread': 'id_thread',
            'comment': 'comment_id',
            'shared_question': 'shared_id'  
        }

        model = model_mapping.get(payload.content_type)
        if model is None:
            return {"success": False, "message": "Invalid content type."}

        model_id = model_id_mapping[payload.content_type]
        reported_object = get_object_or_404(model, **{model_id: payload.reported_object_id})

        if ReportModel.objects.filter(
            reported_by=user,
            reported_type=payload.content_type,
            object_id=reported_object.id_thread
        ).exists():
            return {"success": False, "message": "You have already reported this content."}

        try:
            content_type = ContentType.objects.get_for_model(model)

            max_report_id = ReportModel.objects.aggregate(Max('report_id'))['report_id__max']
            new_report_id = (max_report_id or 0) + 1  

            report = ReportModel.objects.create(
                report_id=new_report_id,
                reported_by=user,
                reported_at=timezone.now(),
                reported_why=payload.reported_why,
                content_type=content_type,
                object_id=reported_object.id_thread,
                reported_type=payload.content_type
            )

            return {"success": True, "report_id": report.report_id, "object_id": report.object_id}

        except Exception as e:
            if 'report' in locals():
                report.delete()

            return {"success": False, "message": f"An error occurred: {str(e)}"}