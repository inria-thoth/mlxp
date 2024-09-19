"""Parser object for querying results stored by the reader."""

import abc
import ast
from operator import eq, ge, gt, le, lt, ne

from ply import lex
from ply import yacc
from tinydb import Query, where
from tinydb.queries import QueryInstance

from mlxp.enumerations import SearchableKeys
from mlxp.errors import InvalidKeyError


class Parser(abc.ABC):
    """An abstract class for parsing queries.

    Any parser used by the class Reader must inherit from this abstract class.
    """

    @abc.abstractmethod
    def parse(self, query: str) -> QueryInstance:
        """Parse a query string into a tinydb QueryInstance object.

        :param query: A query in the form of a string
        :type query: str
        :return: A instance of a QueryInstance class representing the query
        :rtype: QueryInstance
        :raises SyntaxError: if the query string does not follow expected syntax.
        """
        raise NotImplementedError


class DefaultParser(Parser):
    """MLXP's deafult parser inspired from python's syntax."""

    def __init__(self):
        self.lexer = _Lexer()
        self.parser = _YaccParser()

    def parse(self, query: str) -> QueryInstance:
        """Parse a query string into a tinydb QueryInstance object."""
        return self.parser.parse(query, lexer=self.lexer)


ops = {
    "==": eq,
    "!=": ne,
    "<=": le,
    ">=": ge,
    "<": lt,
    ">": gt,
}

tokens = (
    "ID",
    "LIST",
    "SCALAR",
    "EQUAL",
    "LESS_THAN",
    "GREATER_THAN",
    "LESS_THAN_OR_EQUAL",
    "GREATER_THAN_OR_EQUAL",
    "NOT_EQUAL",
    "AND",
    "OR",
    "NOT",
    "LPAREN",
    "RPAREN",
    "IN",
)


def _Lexer():
    reserved = {"in": "IN"}

    # Define regular expressions for each token
    t_EQUAL = r"=="
    t_LESS_THAN_OR_EQUAL = r"<="
    t_GREATER_THAN_OR_EQUAL = r">="
    t_NOT_EQUAL = r"!="
    t_LESS_THAN = r"<"
    t_GREATER_THAN = r">"
    t_AND = r"&"
    t_OR = r"\|"
    t_NOT = r"~"
    t_LPAREN = r"\("
    t_RPAREN = r"\)"
    t_IN = r"in"
    t_ignore = " \t"

    # Define a rule for list literals
    def t_LIST(t):
        r"\[[^\]]*\]"
        t.type = "LIST"  # Update the token type to 'LIST'
        t.value = ast.literal_eval(t.value)  # Evaluate the list literal to create a list object
        return t

    def t_BOOL(t):
        r"(?i:true)|(?i:false)"
        t.type = "SCALAR"
        t.value = ast.literal_eval(t.value)
        return t

    def t_STRING(t):
        r"\'(.*?)\'"
        t.type = "SCALAR"
        t.value = ast.literal_eval(t.value)
        return t

    # Define a rule for scalar values (including integers, floats, and strings)
    def t_SCALAR(t):
        r"([+-]?([0-9]+([.][0-9]*)?|[.][0-9]+))|\'[^\']*\'|\"[^\"]*\" "
        # t.type = 'LIST'
        t.value = ast.literal_eval(t.value)
        return t

    # A regular expression rule with some action code
    def t_ID(t):
        # r'[a-zA-Z][\w._-]*'
        r"[a-zA-Z_\d]+(\.[a-zA-Z_\d]+)*"
        t.type = reserved.get(t.value, "ID")  # Check for reserved words
        return t

    def t_error(t):
        raise SyntaxError(f'Illegal character "{t.value[0]}"')

    return lex.lex(debug=False)


def _YaccParser():
    precedence = (
        ("left", "OR"),
        ("left", "AND"),
        ("left", "NOT"),
        (
            "left",
            "EQUAL",
            "LESS_THAN",
            "GREATER_THAN",
            "LESS_THAN_OR_EQUAL",
            "GREATER_THAN_OR_EQUAL",
            "NOT_EQUAL",
            "IN",
        ),
    )

    def p_expression__bin_op(expr):
        """Expr : ID EQUAL SCALAR
        | ID NOT_EQUAL SCALAR
        | ID LESS_THAN SCALAR
        | ID GREATER_THAN SCALAR
        | ID LESS_THAN_OR_EQUAL SCALAR
        | ID GREATER_THAN_OR_EQUAL SCALAR
        """
        expr[0] = _bin_op(expr[1], expr[2], expr[3])

    def p_expression_inclusion(expr):
        """Expr : ID IN LIST"""
        expr[0] = _inclusion_op(expr[1], expr[3])

    def p_expression_group(expr):
        """Expr : LPAREN Expr RPAREN"""
        expr[0] = expr[2]

    def p_expression_and(expr):
        """Expr : Expr AND Expr"""
        expr[0] = _and_op(expr[1], expr[3])

    def p_expression_or(expr):
        """Expr : Expr OR Expr"""
        expr[0] = _or_op(expr[1], expr[3])

    def p_expression_not(expr):
        """Expr : NOT Expr"""
        expr[0] = _not_op(expr[2])

    def p_error(expr):
        raise SyntaxError(" Syntax error in input!")

    return yacc.yacc(debug=False, write_tables=0)


def _bin_op(key, operation, value):
    opf = ops.get(operation, None)
    if opf is None:
        print("Unknown operator: {0:s}".format(operation))
        raise ValueError
        return where(None)
    _check_searchable_key(key)
    field = _build_field_struct(key)
    return opf(field, value)


def _inclusion_op(key, values):
    _check_searchable_key(key)
    field = _build_field_struct(key)
    return field.one_of(values)


def _and_op(left, right):
    return (left) & (right)


def _or_op(left, right):
    return (left) | (right)


def _not_op(expr):
    return ~expr


def _build_field_struct(key):
    field = Query()
    field = field[key]
    return field


def _is_searchable(key):
    for member in SearchableKeys:
        if key.startswith(member.value):
            return True
    return False


def _check_searchable_key(key):
    if _is_searchable(key):
        pass
    else:
        raise InvalidKeyError(
            f"The key {key} is invalid! Valid keys must start with one of these prefixes: "
            + str([member.value for member in SearchableKeys])
        )
