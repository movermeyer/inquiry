inquiry [![Build Status](https://secure.travis-ci.org/stevepeak/inquiry.png)](http://travis-ci.org/stevepeak/inquiry) [![Version](https://pypip.in/v/inquiry/badge.png)](https://github.com/stevepeak/inquiry) [![Coverage Status](https://coveralls.io/repos/stevepeak/inquiry/badge.png)](https://coveralls.io/r/stevepeak/inquiry) [![codecov.io](https://codecov.io/stevepeak/inquiry.png)](https://codecov.io/stevepeak/inquiry)
-------

`pip install inquiry`


## :seedling: Seeds

> The bread and butter of Figures. Provide any number of seeds at differnt levels to produce amazing Inquirys

Seeds are the following parts of the query: ``select``, ``tables`` and ``where``.
Seeds can be presented anywhere within the Inquiry.


| Key                     | Value                            | Description         |
| :---------------------- | --------------                   | ------------------- |
| `title`                 | `str`                            | short description   |
| `help`                  | `str, url`                       |                     |
| `inherits`              | `str, list`                      |                     |
| `select` or `selects`   | `str, list`                      |                     |
| `with`                  |                                  |                     |
| `table` or `tables`     |                                  |                     |
| `where`                 |                                  |                     |
| `arguments`             | [Arguments](#squirrel-arguments) |                     |


#### Policies

1. All ``arguments`` are inherited from previous lvls
  a. Remove an argument via ``":name": false``
2. Overlaping argumets will override, entirly, the previous lvl argument
3. Index level of the figure must return a list of object ids
  b. optional ``agg`` argument may return aggregate data w/out ids
4. Inheriting other figures will inherit all their ``arguments`` and ``seeds``

#### Methods

There are a few methods available to seed articles (`select`, `tables`, `with`, `where`)

- **Clear** pervious values of all previous articles of this type
```json
    { 
        "select": [false, "sum(totals) as totals"]
    }
```


## :squirrel: Arguments

> Values that users can adjust to query differnt Inquiry results

| Key                     | Value             | Description                                                  |
| :---------------------- | --------------    | -------------------                                          |
| `validator`             |                   |                                                              |
| `pattern`               | ``regexp string`` | to validate the argument                                     |
| `ignores`               | ``"" or []``      | other arguments not allowed to be here                       |
| `require`               | ``"" or []``      | other arguments that are required to be provided to          |
| `required`              | ``bool``          | argument is required to be provided                          |
| `default`               | ``""``            | the value of this argument when **not** provided by the user |
| `adapt`                 | ``bool``          | if the value should be adapted for ``psql``, *defualt true*  |
| `options`               |                   |                                                              |


#### Methods

When arguments are duplicated (which is comonn) the default action is
to **completely** override the previous argument definition. However,
in some cases it is better to append/adjust or reduce the previous
definition.

- Append / Adjust via ``&:key``
  - The previous definition will be adjusted if present or added if not present, respectively.
- Reduce via ``-:key``
  - The previous definition will have definitions removed entirly.
      For this method the argument definition should be a **list** not a dictionary.
