from django.db import models
from urllib.parse import quote_plus
import dateparser


class Email(models.Model):
    date = models.DateTimeField()
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
            date=dateparser.parse(mail.date),
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