from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from urllib.parse import quote_plus


class Email(models.Model):
    date = models.CharField(max_length=100)
    from_address = models.CharField(max_length=200)
    body = models.TextField()
    title = models.CharField(max_length=50)
    uid = models.PositiveIntegerField()
    message_id = models.CharField(max_length=200)

    @classmethod
    def from_mail_object(cls, mail):
        return Email.objects.create(
            body=mail.body,
            title=mail.title,
            date=mail.date,
            from_address=mail.from_addr,
            uid=mail.uid,
            message_id=mail.message_id
        )

    def __str__(self):
        return f'from:{self.from_address} «{self.title}»'

    @property
    def gmail_url(self):
        mid = quote_plus(f':{self.message_id}')
        return f'https://mail.google.com/mail/u/0/#search/rfc822msgid{mid}'


class Attachment(models.Model):
    email = models.ForeignKey('Email', null=True)
    mimetype = models.CharField(max_length=100)
    file = models.FileField(upload_to='attachments/', null=True, blank=True)
    mesa = models.OneToOneField('elecciones.Mesa', null=True, related_name='attachment')
    taken = models.DateTimeField(null=True)

    def __str__(self):
        return f'{self.file} ({self.mimetype})'


@receiver(post_save, sender='elecciones.Mesa')
def marcar_como_testigo(sender, instance=None, created=False, **kwargs):
    """
    cuando se asocia una mesa a un acta o se sube el documento, y es la primera
    de la escuela, la marcamos como testigo
    """
    if not instance.foto_o_attachment and not instance.lugar_votacion.mesa_testigo:
        instance.es_testigo = True
        instance.save(update_fields=['es_testigo'])


@receiver(post_save, sender=Attachment)
def marcar_como_testigo_via_attach(sender, instance=None, created=False, **kwargs):
    """
    cuando se asocia una mesa a un acta o se sube el documento, y es la primera
    de la escuela, la marcamos como testigo
    """
    if instance.mesa and not mesa.lugar_votacion.mesa_testigo:
        mesa = instance.mesa
        mesa.es_testigo = True
        mesa.save(update_fields=['es_testigo'])
