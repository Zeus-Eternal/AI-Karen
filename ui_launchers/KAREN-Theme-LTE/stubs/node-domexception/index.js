const DOMExceptionCtor = typeof globalThis.DOMException === 'function'
  ? globalThis.DOMException
  : class DOMException extends Error {
      constructor(message = '', name = 'Error') {
        super(message)
        this.name = name
      }
    }

export default DOMExceptionCtor
export { DOMExceptionCtor as DOMException }
