package com.levantis.logmyself.ui.utils

import android.content.Context
import android.content.DialogInterface
import androidx.appcompat.app.AlertDialog

object DialogUtils {

    fun showAlertDialog(
        context: Context,
        title: String,
        message: String,
        positiveButtonText: String,
        positiveButtonListener: DialogInterface.OnClickListener? = null,
        negativeButtonText: String? = null,
        negativeButtonListener: DialogInterface.OnClickListener? = null
    ) {
        val builder = AlertDialog.Builder(context)
        builder.setTitle(title)
            .setMessage(message)
            .setPositiveButton(positiveButtonText, positiveButtonListener)

        if (negativeButtonText != null) {
            builder.setNegativeButton(negativeButtonText, negativeButtonListener)
        }

        val dialog = builder.create()
        dialog.show()
    }

    fun showInfoDialog(
        context: Context,
        title: String,
        message: String,
        buttonText: String,
        buttonListener: DialogInterface.OnClickListener? = null
    ) {
        val builder = AlertDialog.Builder(context)
        builder.setTitle(title)
            .setMessage(message)
            .setPositiveButton(buttonText, buttonListener)

        val dialog = builder.create()
        dialog.show()
    }

}