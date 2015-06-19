
documentAttributeImageSize#6c37c15c w:int h:int = DocumentAttribute;
documentAttributeAnimated#11b58939 = DocumentAttribute;
documentAttributeSticker#fb0a5727 = DocumentAttribute;
documentAttributeVideo#5910cccb duration:int w:int h:int = DocumentAttribute;
documentAttributeAudio#51448e5 duration:int = DocumentAttribute;
documentAttributeFilename#15590068 file_name:string = DocumentAttribute;
photoSizeEmpty#e17e23c type:string = PhotoSize;
photoSize#77bfb61b type:string location:FileLocation w:int h:int size:int = PhotoSize;
photoCachedSize#e9a734fa type:string location:FileLocation w:int h:int bytes:bytes = PhotoSize;
fileLocationUnavailable#7c596b46 volume_id:long local_id:int secret:long = FileLocation;
fileLocation#53d69076 dc_id:int volume_id:long local_id:int secret:long = FileLocation;
decryptedMessageMediaExternalDocument#fa95b0dd id:long access_hash:long date:int mime_type:string size:int thumb:PhotoSize dc_id:int attributes:Vector<DocumentAttribute> = DecryptedMessageMedia;
