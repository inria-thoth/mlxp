"""Parser object for querying results stored by the reader."""

import abc
import ast
from operator import eq, ge, gt, le, lt, ne

import ply.lex as lex
import ply.yacc as yacc
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
        pass


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

    def p_expression__binOp(p):
        """Expr : ID EQUAL SCALAR
        | ID NOT_EQUAL SCALAR
        | ID LESS_THAN SCALAR
        | ID GREATER_THAN SCALAR
        | ID LESS_THAN_OR_EQUAL SCALAR
        | ID GREATER_THAN_OR_EQUAL SCALAR
        """
        p[0] = _binOp(p[1], p[2], p[3])

    def p_expression_inclusion(p):
        """Expr : ID IN LIST"""
        p[0] = _inclusionOp(p[1], p[3])

    def p_expression_group(p):
        """Expr : LPAREN Expr RPAREN"""
        p[0] = p[2]

    def p_expression_and(p):
        """Expr : Expr AND Expr"""
        p[0] = _andOp(p[1], p[3])

    def p_expression_or(p):
        """Expr : Expr OR Expr"""
        p[0] = _orOp(p[1], p[3])

    def p_expression_not(p):
        """Expr : NOT Expr"""
        p[0] = _notOp(p[2])

    def p_error(p):
        raise SyntaxError(" Syntax error in input!")

    return yacc.yacc(debug=False, write_tables=0)


def _binOp(k, op, v):
    opf = ops.get(op, None)
    if opf is None:
        print("Unknown operator: {0:s}".format(op))
        raise ValueError
        return where(None)
    _check_searchable_key(k)
    field = _build_field_struct(k)
    return opf(field, v)


def _inclusionOp(key, values):
    _check_searchable_key(key)
    field = _build_field_struct(key)
    return field.one_of(values)


def _andOp(left, right):
    return (left) & (right)


def _orOp(left, right):
    return (left) | (right)


def _notOp(expr):
    return ~expr


def _build_field_struct(key):
    field = Query()
    field = field[key]
    return field


def _is_searchable(k):
    for member in SearchableKeys:
        if k.startswith(member.value):
            return True
    return False


def _check_searchable_key(k):
    if _is_searchable(k):
        pass
    else:
        raise InvalidKeyError(
            f"The key {k} is invalid! Valid keys must start with one of these prefixes: "
            + str([member.value for member in SearchableKeys])
        )
