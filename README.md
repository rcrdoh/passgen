Generador de contraseñas mediante frases o "seedphrases"

Define mentalmente de 2 a 5 palabras mentalmente, usalas como frases que generaran las contraseñas de todos los servicios.
Se pueden elegir 3 tipos de algoritmos de hashing con sus respectivos salts para tener variabilidad de contraseñas en cada servicio.

Lo unico que se guarda son los procesos que se usaron para generar cada contraseña, no se guarda las frases/seedphrases ni las contraseñas finales.


PROCEDIMIENTO DE INSTALACION

instalar environment
python -venv env

activar enviroment. En Linux
source env/bin/activate


//en caso la dependencia no se encuentre en el manejador de paquetes dnf (en este caso pysimplegui no se encuentra en dnf) 
//instalarlo como a continuacion , y configurar el codigo de la aplicacion para consumirlo desde ese directorio
// src/(nombreAplicacion)/(archivosAplicacion)
pip install pysimplegui --target src/passgencli/_vendor

// se le debe dar la estructura adecuada al proyecto de python para ejecutar adecuadamente el python -m build 
// se realizan pruebas de funcionamiento en el env previamente
// previamente instalar la herramienta build : pip install --upgrade build
python -m build

Los siguientes pasos es para que la aplicacion sea ejecutable mediante linea de comandoss en fedora linux

// previamente instalar la herramienta: sudo dnf install rpm-build rpmdevtools
// rpmbuild --define "_topdir $(pwd)/rpmbuild"
rpmdev-setuptree // crea estructura para creacion de rpms, por defecto en directorio home (~)

cp dist/passgencli-1.0.0.tar.gz ~/rpmbuild/SOURCES/

cp dist/passgencli.spec ~/rpmbuild/SPECS/

//dependencias de la aplicacion python deben estar reflejadas mediante comandos dnf install (python_library) en el .spec
//esto se especifica en el archivo .spec para generacion del rpm
rpmbuild -ba ~/rpmbuild/SPECS/passgencli.spec

sudo dnf install ~/rpmbuild/RPMS/noarch/passgencli-*.rpm

//los procedimiento de contraseña son guardados en la extension db.sqlite
//en un sistema linux ~/.local/share/passgencli/