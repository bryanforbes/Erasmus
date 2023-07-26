"""Fix WLC 99 and 151

Revision ID: 3a2b71b2a647
Revises: 2b3acfa18257
Create Date: 2023-07-25 13:11:25.020130

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3a2b71b2a647'
down_revision = '2b3acfa18257'
branch_labels = None
depends_on = None

confessions = sa.table(
    'confessions',
    sa.column('id', sa.Integer),
    sa.column('command', sa.String),
)

confession_sections = sa.table(
    'confession_sections',
    sa.column('confession_id', sa.Integer),
    sa.column('number', sa.Integer),
    sa.column('text', sa.Text),
)


def upgrade():
    conn = op.get_bind()

    confession = conn.execute(
        sa.select(confessions).filter(confessions.c.command == 'wlc')
    ).first()

    op.execute(
        confession_sections.update()
        .filter(confession_sections.c.confession_id == confession.id)
        .filter(confession_sections.c.number == 99)
        .values(
            text='For the right understanding of the Ten Commandments, these rules are to be observed:\n\n1. That the law is perfect, and bindeth everyone to full conformity in the whole man unto the righteousness thereof, and unto entire obedience forever; so as to require the utmost perfection of every duty, and to forbid the least degree of every sin.\n2. That it is spiritual, and so reacheth the understanding, will, affections, and all other powers of the soul; as well as words, works, and gestures.\n3. That one and the same thing, in divers respects, is required or forbidden in several commandments.\n4. That as, where a duty is commanded, the contrary sin is forbidden; and, where a sin is forbidden, the contrary duty is commanded: so, where a promise is annexed, the contrary threatening is included; and, where a threatening is annexed, the contrary promise is included.\n5. That what God forbids, is at no time to be done; what he commands, is always our duty; and yet every particular duty is not to be done at all times.\n6. That under one sin or duty, all of the same kind are forbidden or commanded; together with all the causes, means, occasions, and appearances thereof, and provocations thereunto.\n7. That what is forbidden or commanded to ourselves, we are bound, according to our places to endeavour that it may be avoided or performed by others, according to the duty of their places.\n8. That in what is commanded to others, we are bound, according to our places and callings, to be helpful to them; and to take heed of partaking with others in what is forbidden them.'  # noqa: E501
        )
    )

    op.execute(
        confession_sections.update()
        .filter(confession_sections.c.confession_id == confession.id)
        .filter(confession_sections.c.number == 151)
        .values(
            text="Sins receive their aggravations,\n\n1. From the persons offending if they be of riper age, greater experience or grace, eminent for profession, gifts, place, office, guides to others, and whose example is likely to be followed by others.\n2. From the parties offended: if immediately against God, his attributes, and worship; against Christ, and his grace; the Holy Spirit, his witness, and workings against superiors, men of eminency, and such as we stand especially related and engaged unto; against any of the saints, particularly weak brethren, the souls of them, or any other, and the common good of all or many.\n3. From the nature and quality of the offense: if it be against the express letter of the law, break many commandments, contain in it many sins: if not only conceived in the heart, but breaks forth in words and actions, scandalize others, and admit of no reparation: if against means, mercies, judgments, light of nature, conviction of conscience, public or private admonition, censures of the church, civil punishments; and our prayers, purposes, promises, vows, covenants, and engagements to God or men: if done deliberately, wilfully, presumptuously, impudently, boastingly, maliciously, frequently, obstinately, with delight, continuance, or relapsing after repentance.\n4. From circumstances of time and place: if on the Lord's day, or other times of divine worship; or immediately before or after these, or other helps to prevent or remedy such miscarriages; if in public, or in the presence of others, who are thereby likely to be provoked or defiled."  # noqa: E501
        )
    )


def downgrade():
    conn = op.get_bind()

    confession = conn.execute(
        sa.select(confessions).filter(confessions.c.command == 'wlc')
    ).fetchone()

    op.execute(
        confession_sections.update()
        .filter(confession_sections.c.confession_id == confession.id)
        .filter(confession_sections.c.number == 99)
        .values(
            text='For the right understanding of the Ten Commandments, these rules are '
            'to be observed:'
        )
    )

    op.execute(
        confession_sections.update()
        .filter(confession_sections.c.confession_id == confession.id)
        .filter(confession_sections.c.number == 151)
        .values(text='Sins receive their aggravations,')
    )
