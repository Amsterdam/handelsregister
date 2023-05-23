#!/usr/bin/env python
description = """
Utility for outputting SQL used to load data
from the reference database into the legacy handelsregister database.

The data transfer happens in a single transaction. Partial transfer
in separate transactions can only be done by making separate CLI
invocations with table arguments.

 Note that dimensions and primary keys between "corresponding" 
 tables are not always the same, so we need to make a case-by-case
 decision on how to map ref-db entries to the handelsregister entries.
 These decisions are clarified below:
"""

import argparse
import logging
import sys
from typing import List, Tuple, Dict

from psycopg2 import connect, sql
from psycopg2.extensions import connection as Connection


logger = logging.getLogger("refdb-loading-script")
SOURCE_SCHEMA = "public"
TARGET_SCHEMA = "handelsregister"


def with_query_body(
    ctes: List[Tuple[str, sql.SQL, Dict[str, sql.Composable]]]
) -> sql.SQL:
    """Construct a WITH query body composed of the given common table
    expressions (CTEs) and corresponding aliases.

    The CTEs are supplied through a SQL object which accepts a Dict of Composables
    as formatting parameters.

    Parameters:
        * ctes: a list of tuples of (alias, cte SQL, cte SQL args)
    """
    return sql.SQL(", ").join(
        [
            sql.SQL("{alias} AS ({cte})").format(
                cte=cte.format(**kwargs),
                alias=sql.Identifier(alias),
            )
            for (alias, cte, kwargs) in ctes
        ]
    )


truncate_stmt = sql.SQL("TRUNCATE {target_schema}.{target_table} CASCADE")

# NOTE: entries in this dict literal dictate the correct loading order.
table_registry = {
    # tables without FKs
    "hr_commercielevestiging": [],
    "hr_communicatiegegevens": [],
    "hr_dataselectie": [],
    "hr_handelsnaam": [],
    "hr_kapitaal": [],
    "hr_locatie": [],
    "hr_nietcommercielevestiging": [],
    "hr_rechterlijkeuitspraak": [],
    "sbicodes_sbicodehierarchy": [],
    # tables with FKs
    "hr_activiteit": [],
    "hr_functievervulling": [],
    "hr_geovestigingen": [],
    "hr_maatschappelijkeactiviteit": [],
    "hr_maatschappelijkeactiviteit_activiteiten": [],
    "hr_maatschappelijkeactiviteit_communicatiegegevens": [],
    "hr_natuurlijkpersoon": [],
    "hr_nietnatuurlijkpersoon": [],
    "hr_onderneming": [],
    "hr_onderneming_handelsnamen": [],
    "hr_persoon": [],
    "hr_vestiging": [],
    "hr_vestiging_activiteiten": [],
    "hr_vestiging_communicatiegegevens": [],
    "hr_vestiging_handelsnamen": [],
}


parser = argparse.ArgumentParser(description=description)
parser.add_argument("-v", "--verbose", action="store_true")

parser.add_argument("-H", "--host", default="localhost", help="db host")
parser.add_argument("-P", "--port", default="5432", help="db port")
parser.add_argument("-D", "--database", default="dataservices", help="db")
parser.add_argument("-U", "--user", default="dataservices", help="db user")
parser.add_argument("-p", "--password", default="insecure", help="db pwd")

parser.add_argument(
    "tables",
    nargs="*",
    help="""
        Database names of the tables in handelsregister to generate SQL for.
        If ommitted, generate SQL for all tables.
    """,
    default=list(
        table_registry
    ),  # rely on dict insertion to guarantee the correct loading order
)
parser.add_argument(
    "--delete",
    help="Truncate the specified tables in handelsregister",
    action="store_true",
)
parser.add_argument(
    "--execute",
    help="If ommitted, only emit statements that would be executed to stdout",
    action="store_true",
)
parser.add_argument(
    "-S",
    "--show-tables",
    help="Show allowed target tables and exit.",
    action="store_true",
)


def main(tables: List[str], connection: Connection, execute: bool, delete: bool):
    with connection.cursor() as cursor:
        for table in tables:
            if delete:
                statements = [
                    truncate_stmt.format(
                        target_table=sql.Identifier(table),
                        target_schema=sql.Identifier(TARGET_SCHEMA),
                    ),
                ]
            else:
                statements = table_registry[table]

            n_statements = len(statements)
            for i, statement in enumerate(statements):
                if execute:
                    logger.info(
                        "Running (%d/%d) transfer for table %s", i, n_statements, table
                    )
                    cursor.execute(statement)
                    logger.info("Inserted %d rows into %s", cursor.rowcount, table)
                    logger.info("status: %s", cursor.statusmessage)
                else:
                    sys.stdout.write(str(statement.as_string(cursor)))
                    sys.stdout.write("\n")


if __name__ == "__main__":
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.show_tables:
        print("\n".join(table_registry))
        sys.exit()

    with connect(
        database=args.database,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port,
    ) as connection:
        main(args.tables, connection, args.execute, args.delete)
