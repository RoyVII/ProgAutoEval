# ProgAutoEval

## Ejecución

Consiste en dos ficheros: AutoEval.py, que tiene toda la funcionalidad, y runAutoEval.py que ejecuta el programa. El comando para ejecutarlo sería:

> python runAutoEval.py <lista_de_pruebas\>.csv

Los ficheros de python deben colocarse en el mismo directorio en el que se encuentren las carpetas para cada entrega. Por ejemplo:

<pre>
--- P1/
   |--- AutoEval.py
   |--- runAutoEval.py
   |--- solution/
   |--- pareja1/
   |--- pareja2/
   |--- ...
   |--- parejaN/
</pre>

## Requisitos

### Python
Se necesita Python3 solamente, no utiliza ninguna librería especial.

### Solución
En el mismo directorio donde están las entregas de los estudiantes deberá existir una carpeta llamada **solution** con el código que se utilizará para generar las salidas correctas de cada prueba.

### Lista de pruebas

El fichero que se pasa como argumento tendrá la lista de pruebas a realizar, siguiendo el siguiente formato:

- **Tipo:** puede ser *main* o *library*, en función de si se quiere probar un main o una librería. **Obligatorio**.
- **Nombre:** nombre del ejercicio a probar. E.g. "p1_e1" **Obligatorio**.
- **Ficheros fuente:** lista separada por espacios. E.g. "node.c graph.c"
- **Directorios de librerías:** lista separada por espacios. E.g. "-L. -L/home"
- **Librerías:** lista separada por espacios. E.g. "-lm -lstack_fp"
- **Fichero main:** si se quiere probar un main indicar el fichero. E.g. "p1_e1.c"
- **Argumentos de entrada:** lista separada por espacios. E.g. "g1.txt 111 222"

Cada campo estará separado por comas. Un ejemplo de fichero sería el siguiente:
<pre>
type,exerciseName,sourceFiles,libDirs,libs,mainFile,inputArguments
library,node,node.c,,,,
main,p1_e1,node.c,,,p1_e1.c,
library,graph,node.c graph.c,,,,
main,p1_e2,graph.c,,,p1_e2.c,
main,p1_e3,node.c graph.c,,,p1_e3.c,g1.txt
</pre>


### Plantillas
En el caso de que la prueba sea de tipo **library** el programa buscará en su mismo directorio una plantilla con la que generar los distintos mains de pruebas a utilizar. Esta plantilla debe llamarse `template_<exerciseName>.txt`, donde *exerciseName* es el nombre del ejercicio a probar que figura en la lista de pruebas.


## Funcionamiento
El programa ejecutará todas las pruebas de la lista sobre cada entrega. En la carpeta correspondiente a cada entrega generará un informe en formato Markdown (.md) para cada prueba. En el se detallará el proceso de compilación, enlazado, ejecución, comparación de la salida (con respecto al código de **solution**) y ejecución de Valgrind para cada prueba.