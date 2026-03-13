declare module 'nodemailer' {
  export interface Transporter {
    sendMail(mailOptions: MailOptions): Promise<MailResponse>;
  }
  
  export interface MailOptions {
    from?: string;
    to: string | string[];
    subject: string;
    text?: string;
    html?: string;
    attachments?: any[];
    replyTo?: string;
  }
  
  export interface MailResponse {
    messageId: string;
    response: string;
    envelope: any;
    accepted: string[];
    rejected: string[];
    pending: string[];
  }
  
  export interface TransportOptions {
    host?: string;
    port?: number;
    secure?: boolean;
    auth?: {
      user: string;
      pass: string;
    };
  }
  
  export function createTransport(options: TransportOptions): Transporter;
  
  export function verify(transporter: Transporter): Promise<boolean>;
}