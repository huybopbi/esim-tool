(
    WAITING_SM_DP_LINK,
    WAITING_ACTIVATION_CODE_LINK,
    WAITING_SM_DP_QR,
    WAITING_ACTIVATION_CODE_QR,
    WAITING_QR_DATA,
    WAITING_QR_IMAGE,
    WAITING_LPA_STRING,
    WAITING_ADD_ESIM_SM_DP,
    WAITING_ADD_ESIM_CODE,
    WAITING_ADD_ESIM_DESC,
    WAITING_ESIM_SELECTION,
    WAITING_ADD_ESIM_LPA,
    WAITING_ADD_ESIM_LPA_DESC,
    WAITING_ADD_ESIM_URL,
    WAITING_ADD_ESIM_URL_DESC,
) = range(15)

PUBLIC_CALLBACKS = {
    "android_guide",
    "back_to_menu",
    "check_device",
    "create_link_qr",
    "guide_menu",
    "iphone_guide",
    "support",
}
