import { gql } from "@apollo/client";


export const ENTIDADES = gql`
  query Entidades($limite: Int, $desde: Int!) {
    entidades(limite: $limite, desde: $desde) {
      items {
        id
        nombre
        priApellido
        segApellido
        documento
        tipoEntidad {
          nombre
        }
        tipoDocumento {
          nombre
        }
        estado {
          nombre
        }
      }
      info {
        total
        limite
        desde
        haySiguiente
      }
    }
  }
`;


export const ENTIDAD = gql`
  query Entidad($id: ID!) {
    entidad(id: $id) {
      id
      nombre
      priApellido
      segApellido
      documento
      regimenTributario {
        id
        nombre
      }
      tipoEntidad {
        id
        nombre
      }
      tipoDocumento {
        id
        nombre
      }
      estado {
        id
        nombre
      }
      roles {
        id
        tipoRol {
          id
          nombre
        }
        categoria {
          id
          nombre
        }
        limiteCredito
        estado {
          id
          nombre
        }
      }
      direcciones {
        id
        tipo {
          id
          nombre
        }
        calle
        numero
        descripcion
        direccionTexto
        estado {
          id
          nombre
        }
      }
      contactos {
        id
        nombre
        cargo
        email
        telefono
        estado {
          id
          nombre
        }
      }
    }
  }
`;


export const ENTIDAD_POR_DOCUMENTO = gql`
  query EntidadPorDocumento($documento: String!) {
    entidadPorDocumento(documento: $documento) {
      id
      nombre
      priApellido
      segApellido
      documento
    }
  }
`;


export const CATEGORIAS_ENTIDAD = gql`
  query CategoriasEntidad {
    categoriasEntidad {
      id
      nombre
      descripcion
      descuentoCategCliente
      listaPrecioId
      estado {
        id
        nombre
      }
    }
  }
`;
